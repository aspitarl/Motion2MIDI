import json


class SnapshotManager:
    SCHEMA_VERSION = 1

    def __init__(self, main_window):
        self.main_window = main_window

    def build_snapshot(self):
        geometry = self.main_window.geometry()
        controllers = []
        for slot, widget in enumerate(self._get_controller_widgets(), start=1):
            controllers.append(widget.get_state_dict(slot=slot))

        return {
            "schema_version": self.SCHEMA_VERSION,
            "controllers": controllers,
            "app_state": {
                "geometry": {
                    "x": geometry.x(),
                    "y": geometry.y(),
                    "width": geometry.width(),
                    "height": geometry.height(),
                },
                "show_distance_layout": self.main_window.show_distance_layout_action.isChecked(),
                "show_osc_layout": self.main_window.show_osc_layout_action.isChecked(),
                "always_on_top": self.main_window.always_on_top_action.isChecked(),
                "range_set_mode": self.main_window.range_set_action.isChecked(),
            },
            "distance_state": self.main_window.distance_layout.get_state_dict(),
            "osc_state": self.main_window.osc_preset_layout.get_state_dict(),
        }

    def save_to_file(self, file_path):
        snapshot = self.build_snapshot()
        with open(file_path, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, indent=4)
        return snapshot

    def load_from_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as handle:
            snapshot = json.load(handle)
        return self.apply_snapshot(snapshot)

    def apply_snapshot(self, snapshot):
        controller_states = snapshot.get("controllers", [])
        self._ensure_controller_count(len(controller_states))

        summary = {
            "controller_slots": len(controller_states),
            "connected_slots": 0,
            "disconnected_slots": 0,
            "missing_devices": [],
            "missing_midi_ports": [],
            "errors": [],
        }

        for widget, controller_state in zip(self._get_controller_widgets(), controller_states):
            try:
                result = widget.apply_state_dict(controller_state)
            except Exception as exc:
                summary["errors"].append(f"{widget.name}: {exc}")
                continue

            if result.get("connected"):
                summary["connected_slots"] += 1
            else:
                summary["disconnected_slots"] += 1

            if not result.get("device_matched", True):
                requested_device = result.get("requested_device")
                if requested_device:
                    summary["missing_devices"].append(requested_device)

            if not result.get("midi_port_matched", True):
                requested_port = result.get("requested_midi_port")
                if requested_port:
                    summary["missing_midi_ports"].append(requested_port)

            summary["errors"].extend(result.get("errors", []))

        distance_result = self.main_window.distance_layout.apply_state_dict(snapshot.get("distance_state", {}))
        if not distance_result.get("midi_port_matched", True):
            requested_port = distance_result.get("requested_midi_port")
            if requested_port:
                summary["missing_midi_ports"].append(requested_port)

        self.main_window.osc_preset_layout.apply_state_dict(snapshot.get("osc_state", {}))
        self._apply_app_state(snapshot.get("app_state", {}))
        self.main_window.update_title()

        return summary

    def _get_controller_widgets(self):
        controller_widgets = self.main_window.window_manager_layout.controller_widgets
        return [controller_widgets[name] for name in sorted(controller_widgets, key=self._controller_sort_key)]

    def _controller_sort_key(self, name):
        suffix = name.rsplit(" ", 1)[-1]
        if suffix.isdigit():
            return int(suffix)
        return name

    def _ensure_controller_count(self, target_count):
        controller_widgets = self.main_window.window_manager_layout.controller_widgets
        while len(controller_widgets) < target_count:
            self.main_window.window_manager_layout.add_controller_widget()
            controller_widgets = self.main_window.window_manager_layout.controller_widgets

        while len(controller_widgets) > target_count:
            widget_name = sorted(controller_widgets, key=self._controller_sort_key)[-1]
            self.main_window.window_manager_layout.remove_controller_widget(widget_name)
            controller_widgets = self.main_window.window_manager_layout.controller_widgets

    def _apply_app_state(self, app_state):
        geometry = app_state.get("geometry", {})
        if geometry:
            self.main_window.setGeometry(
                geometry.get("x", self.main_window.x()),
                geometry.get("y", self.main_window.y()),
                geometry.get("width", self.main_window.width()),
                geometry.get("height", self.main_window.height()),
            )

        self._apply_action_state(
            self.main_window.show_distance_layout_action,
            self.main_window.toggle_distance_layout,
            app_state.get("show_distance_layout", self.main_window.show_distance_layout_action.isChecked()),
        )
        self._apply_action_state(
            self.main_window.show_osc_layout_action,
            self.main_window.toggle_osc_layout,
            app_state.get("show_osc_layout", self.main_window.show_osc_layout_action.isChecked()),
        )
        self._apply_action_state(
            self.main_window.always_on_top_action,
            self.main_window.toggle_always_on_top,
            app_state.get("always_on_top", self.main_window.always_on_top_action.isChecked()),
        )
        self._apply_action_state(
            self.main_window.range_set_action,
            self.main_window.toggle_range_set_mode,
            app_state.get("range_set_mode", self.main_window.range_set_action.isChecked()),
        )

    def _apply_action_state(self, action, callback, checked):
        if action.isChecked() == checked:
            return
        action.blockSignals(True)
        action.setChecked(checked)
        action.blockSignals(False)
        callback(checked)