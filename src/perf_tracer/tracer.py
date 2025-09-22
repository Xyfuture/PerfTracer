"""
Tracer module for creating Perfetto-compatible trace events.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
import json
from contextlib import contextmanager


@dataclass
class _OpenEvent:
    """Represents an open event that has been started but not yet ended."""
    name: str
    ts_us: float

@dataclass(frozen=True,eq=True)
class ModuleInfo:
    pid:int = 1
    module_name:str = 'default'



@dataclass(frozen=True,eq=True)
class TrackInfo:
    module_info:ModuleInfo = field(default_factory=ModuleInfo)
    tid:int = -1
    track_name:str = ''
    

    @property
    def pid(self) -> int:
        return self.module_info.pid
    
    @property
    def module_name(self) -> str:
        return self.module_info.module_name 
    

class PerfettoTracer:
    """
    PerfettoTracer emits the Chrome Trace Event JSON format, which Perfetto can import.


    说明:
    - 层次结构, module 对应 perfetto 中的 process, track 对应 perfetto 中的 thread
    - 传入的 cycles 会按: cycles * ns_per_cycle / 1000.0 -> 微秒(us) 存入 JSON.
    - 可使用 get_global_tracer() 获取全局实例，使用 init_global_tracer() 初始化全局实例
    """
    
    _global_instance: Optional[PerfettoTracer] = None

    def __init__(
        self,
        ns_per_cycle: float = 1.0,
    ) -> None:
        """
        Initialize the PerfettoTracer.

        Args:
            ns_per_cycle: 1 个周期等于多少纳秒 (可为浮点数, 如 0.5 表示 1 cycle = 0.5 ns).
            pid: 进程 ID.
        """
        self.ns_per_cycle = float(ns_per_cycle)
        # 内部换算: cycle -> us
        # us = cycles * ns_per_cycle / 1000
        self._cycle_to_us = self.ns_per_cycle / 1000.0

        self._next_tid = 1000
        self._next_pid = 100000

        # 记录所有 track info 和 module info，防止重复注册
        self._registered_modules: Dict[str, ModuleInfo] = {}
        self._registered_tracks: Dict[str, TrackInfo] = {}

        self._open_events: Dict[TrackInfo, List[_OpenEvent]] = {}
        self._events: List[Dict[str, Any]] = []

    def _cycles_to_us(self, cycles: float) -> float:
        """把 cycles 换算为微秒(us)."""
        return float(cycles) * self._cycle_to_us

    def register_module(self, module_name: str) -> ModuleInfo:
        """创建一个 module, 对应 perfetto 中的 process , 返回 ModuleInfo"""
        if module_name in self._registered_modules:
            return self._registered_modules[module_name]

        pid = self._next_pid
        self._next_pid += 1

        module_info = ModuleInfo(pid=pid, module_name=module_name)

        # 记录到注册表
        self._registered_modules[module_name] = module_info

        # 添加进程元数据
        self._events.append({
            "ph": "M",
            "pid": pid,
            "name": "process_name",
            "args": {"name": module_name},
        })

        return module_info 

    def register_track(self, track_name: str, module_info: Optional[ModuleInfo] = None) -> TrackInfo:
        """创建一个 track, 对应 perfetto 中的 thread, 返回一个TrackInfo"""

        if module_info is None:
            # Ensure the default module is registered
            module_info = self.register_module("default")

        # 构造唯一的 track key: module_name.track_name
        track_key = f"{module_info.module_name}.{track_name}"

        if track_key in self._registered_tracks:
            return self._registered_tracks[track_key]

        tid = self._next_tid
        self._next_tid += 1

        track_info = TrackInfo(
            module_info=module_info,
            tid=tid,
            track_name=track_name
        )

        # 记录到注册表
        self._registered_tracks[track_key] = track_info

        # 初始化该 track 的 open events 栈
        self._open_events[track_info] = []

        # 添加线程元数据
        self._events.append({
            "ph": "M",
            "pid": module_info.pid,
            "tid": tid,
            "name": "thread_name",
            "args": {"name": track_name},
        })

        return track_info


    def start_event(self, track_info:TrackInfo, ts_cycles: float, event_name: str, category: Optional[str] = None) -> None:
        """
        开始一个带作用域的事件 (B). ts_cycles 以 cycles 为单位.
        必须与 end_event() 匹配 (同一 tid 栈式配对).
        """
        ts_us = self._cycles_to_us(ts_cycles)

        self._events.append({
            "ph": "B",
            "pid": track_info.pid,
            "tid": track_info.tid,
            "ts": ts_us,
            "name": event_name,
            "cat": category,
        })
        self._open_events[track_info].append(_OpenEvent(name=event_name, ts_us=ts_us))

    def end_event(self,  track_info: TrackInfo, ts_cycles: float, name: Optional[str] = None, category: Optional[str] = None) -> None:
        """
        结束最近打开的事件(E) ts_cycles 以 cycles 为单位
        如果提供 name 参数, 会检查和栈顶事件的 name 是否一致
        """
        if track_info not in self._open_events or not self._open_events[track_info]:
            raise ValueError(f"No open events for track {track_info.track_name}")

        open_event = self._open_events[track_info][-1]

        if name is not None and open_event.name != name:
            raise ValueError(f"Expected to close event '{open_event.name}', but got '{name}'")

        ts_us = self._cycles_to_us(ts_cycles)

        self._events.append({
            "ph": "E",
            "pid": track_info.pid,
            "tid": track_info.tid,
            "ts": ts_us,
            "cat": category,
        })
        self._open_events[track_info].pop()

    def complete_event(
        self,
        track_info: TrackInfo,
        start_ts: float,
        end_ts: Optional[float] = None,
        dur: Optional[float] = None,
        name: str = "",
        category: Optional[str] = None,
    ) -> None:
        """
        插入一个完整事件 (X). 所有时间参数均为 cycles.
        传 (start_ts + end_ts) 或 (start_ts + dur) 二选一.
        """
        start_us = self._cycles_to_us(start_ts)

        if (end_ts is None) == (dur is None):
            raise ValueError("Provide exactly one of end_ts or dur")

        if dur is None:
            dur_us = self._cycles_to_us(end_ts) - start_us  # type: ignore[arg-type]
        else:
            dur_us = self._cycles_to_us(dur)

        if dur_us < 0:
            raise ValueError("Duration is negative; check start/end timestamps.")

        self._events.append({
            "ph": "X",
            "pid": track_info.pid,
            "tid": track_info.tid,
            "ts": start_us,
            "dur": dur_us,
            "name": name,
            "cat": category,
        })

    def save(self, path: str, display_time_unit: str = "ns") -> None:
        """
        写出 Chrome Trace Event JSON.
        display_time_unit: "ns" | "us" | "ms" | "s"
        仅影响 UI 展示, 不影响数据本身 (我们内部仍用 us 存 ts/dur).
        """
        # 允许存在未闭合的 B 事件; 一般是生产端 Bug, Perfetto 仍能加载.
        doc = {
            "traceEvents": self._events,
            "displayTimeUnit": display_time_unit,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def init_global_tracer(
        cls,
        ns_per_cycle: float = 1.0,
    ) -> PerfettoTracer:
        """
        初始化全局 PerfettoTracer 实例。

        Args:
            ns_per_cycle: 1 个周期等于多少纳秒

        Returns:
            初始化的 PerfettoTracer 实例
        """
        cls._global_instance = cls(ns_per_cycle=ns_per_cycle)
        return cls._global_instance

    @classmethod
    def get_global_tracer(cls) -> PerfettoTracer:
        """
        获取全局 PerfettoTracer 实例。
        
        Returns:
            全局 PerfettoTracer 实例
            
        Raises:
            RuntimeError: 如果全局实例尚未初始化
        """
        if cls._global_instance is None:
            raise RuntimeError("Global PerfettoTracer instance has not been initialized. Call init_global() first.")
        return cls._global_instance

    @contextmanager
    def record_event(self, track_info: TrackInfo, time_fn: Callable[[], float], name: str, category: Optional[str] = None):
        """
        Context manager for recording a scoped event (B/E).

        Args:
            track_info: TrackInfo 实例
            time_fn: 返回当前时间 (cycles) 的函数
            name: 事件名称
            category: 事件分类
        """
        start_cycles = time_fn()
        self.start_event(track_info, start_cycles, name, category)
        try:
            yield None
        finally:
            end_cycles = time_fn()
            self.end_event(track_info, end_cycles)

    def get_module(self, module_name: str) -> Optional[ModuleInfo]:
        """获取已注册的模块信息"""
        return self._registered_modules.get(module_name)

    def get_track(self, track_name: str, module_name: str = "default") -> Optional[TrackInfo]:
        """获取已注册的轨道信息"""
        track_key = f"{module_name}.{track_name}"
        return self._registered_tracks.get(track_key)

    def list_modules(self) -> List[str]:
        """列出所有已注册的模块名称"""
        return list(self._registered_modules.keys())

    def list_tracks(self) -> List[str]:
        """列出所有已注册的轨道名称 (格式: module_name.track_name)"""
        return list(self._registered_tracks.keys())