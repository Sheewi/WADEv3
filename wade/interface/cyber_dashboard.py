# -*- coding: utf-8 -*-
"""
WADE Cyber Dashboard
Futuristic JARVIS-style interface with scattered widgets and holographic elements.
"""

import os
import sys
import json
import time
import threading
import math
import random
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk, Canvas, Frame, Label, Button
import tkinter.font as tkFont


@dataclass
class WidgetConfig:
    """Configuration for dashboard widgets."""

    widget_id: str
    widget_type: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    title: str
    data_source: Optional[Callable] = None
    update_interval: int = 1000
    style: Dict = None
    interactive: bool = True
    floating: bool = True


class CyberTheme:
    """Cyber theme configuration and styling."""

    # Color palette inspired by the images
    COLORS = {
        "bg_primary": "#000000",  # Deep black background
        "bg_secondary": "#0a0a0a",  # Slightly lighter black
        "bg_widget": "#111111",  # Widget background
        "accent_cyan": "#00ffff",  # Bright cyan
        "accent_blue": "#0080ff",  # Electric blue
        "accent_orange": "#ff8000",  # Orange highlights
        "accent_white": "#ffffff",  # Pure white
        "text_primary": "#00ffff",  # Cyan text
        "text_secondary": "#80c0ff",  # Light blue text
        "text_dim": "#4080c0",  # Dimmed blue text
        "border_glow": "#00ffff",  # Glowing borders
        "warning": "#ffaa00",  # Warning orange
        "error": "#ff4040",  # Error red
        "success": "#00ff80",  # Success green
        "grid_lines": "#002040",  # Grid line color
        "hologram": "#0040ff",  # Holographic blue
    }

    # Fonts
    FONTS = {
        "title": ("Orbitron", 16, "bold"),
        "subtitle": ("Orbitron", 12, "bold"),
        "body": ("Consolas", 10, "normal"),
        "mono": ("Courier New", 9, "normal"),
        "large": ("Orbitron", 20, "bold"),
        "small": ("Consolas", 8, "normal"),
    }

    # Animation settings
    ANIMATION = {
        "glow_speed": 0.05,
        "pulse_speed": 0.03,
        "rotation_speed": 0.02,
        "fade_speed": 0.1,
        "particle_speed": 2,
    }

    # Widget styles
    WIDGET_STYLES = {
        "circular": {
            "shape": "circle",
            "border_width": 2,
            "glow_radius": 5,
            "inner_padding": 10,
        },
        "hexagonal": {
            "shape": "hexagon",
            "border_width": 3,
            "glow_radius": 8,
            "inner_padding": 15,
        },
        "rectangular": {
            "shape": "rectangle",
            "border_width": 1,
            "glow_radius": 3,
            "inner_padding": 8,
        },
        "holographic": {
            "shape": "circle",
            "border_width": 0,
            "glow_radius": 15,
            "inner_padding": 20,
            "transparency": 0.7,
        },
    }


class AnimatedWidget:
    """Base class for animated dashboard widgets."""

    def __init__(self, canvas: Canvas, config: WidgetConfig, theme: CyberTheme):
        self.canvas = canvas
        self.config = config
        self.theme = theme
        self.x, self.y = config.position
        self.width, self.height = config.size
        self.elements = []
        self.animation_frame = 0
        self.last_update = 0
        self.data = {}
        self.visible = True
        self.glow_intensity = 0
        self.pulse_phase = random.random() * math.pi * 2

        # Create widget elements
        self._create_widget()

        # Start animation
        self._animate()

    def _create_widget(self):
        """Create the widget visual elements."""
        style = self.config.style or self.theme.WIDGET_STYLES["circular"]

        # Create background
        self._create_background(style)

        # Create border and glow effect
        self._create_border_glow(style)

        # Create content area
        self._create_content(style)

        # Create title
        self._create_title()

    def _create_background(self, style: Dict):
        """Create widget background."""
        if style["shape"] == "circle":
            radius = min(self.width, self.height) // 2
            self.bg_element = self.canvas.create_oval(
                self.x - radius,
                self.y - radius,
                self.x + radius,
                self.y + radius,
                fill=self.theme.COLORS["bg_widget"],
                outline="",
                width=0,
            )
        elif style["shape"] == "hexagon":
            points = self._calculate_hexagon_points()
            self.bg_element = self.canvas.create_polygon(
                points, fill=self.theme.COLORS["bg_widget"], outline="", width=0
            )
        else:  # rectangle
            self.bg_element = self.canvas.create_rectangle(
                self.x - self.width // 2,
                self.y - self.height // 2,
                self.x + self.width // 2,
                self.y + self.height // 2,
                fill=self.theme.COLORS["bg_widget"],
                outline="",
                width=0,
            )

        self.elements.append(self.bg_element)

    def _create_border_glow(self, style: Dict):
        """Create glowing border effect."""
        border_width = style["border_width"]
        glow_radius = style["glow_radius"]

        # Create multiple glow layers for depth
        for i in range(glow_radius):
            alpha = 1.0 - (i / glow_radius)
            color = self._blend_colors(
                self.theme.COLORS["border_glow"],
                self.theme.COLORS["bg_primary"],
                alpha * 0.3,
            )

            if style["shape"] == "circle":
                radius = min(self.width, self.height) // 2 + i
                glow_element = self.canvas.create_oval(
                    self.x - radius,
                    self.y - radius,
                    self.x + radius,
                    self.y + radius,
                    fill="",
                    outline=color,
                    width=1,
                )
            elif style["shape"] == "hexagon":
                points = self._calculate_hexagon_points(i)
                glow_element = self.canvas.create_polygon(
                    points, fill="", outline=color, width=1
                )
            else:  # rectangle
                glow_element = self.canvas.create_rectangle(
                    self.x - self.width // 2 - i,
                    self.y - self.height // 2 - i,
                    self.x + self.width // 2 + i,
                    self.y + self.height // 2 + i,
                    fill="",
                    outline=color,
                    width=1,
                )

            self.elements.append(glow_element)

    def _create_content(self, style: Dict):
        """Create widget content area."""
        padding = style["inner_padding"]

        # Content background
        if style["shape"] == "circle":
            radius = min(self.width, self.height) // 2 - padding
            self.content_element = self.canvas.create_oval(
                self.x - radius,
                self.y - radius,
                self.x + radius,
                self.y + radius,
                fill=self.theme.COLORS["bg_secondary"],
                outline="",
                width=0,
            )
        else:
            self.content_element = self.canvas.create_rectangle(
                self.x - self.width // 2 + padding,
                self.y - self.height // 2 + padding,
                self.x + self.width // 2 - padding,
                self.y + self.height // 2 - padding,
                fill=self.theme.COLORS["bg_secondary"],
                outline="",
                width=0,
            )

        self.elements.append(self.content_element)

    def _create_title(self):
        """Create widget title."""
        title_y = self.y - self.height // 2 - 20
        self.title_element = self.canvas.create_text(
            self.x,
            title_y,
            text=self.config.title,
            fill=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["subtitle"],
            anchor="center",
        )
        self.elements.append(self.title_element)

    def _calculate_hexagon_points(self, offset: int = 0) -> List[int]:
        """Calculate hexagon points."""
        radius = min(self.width, self.height) // 2 + offset
        points = []

        for i in range(6):
            angle = i * math.pi / 3
            x = self.x + radius * math.cos(angle)
            y = self.y + radius * math.sin(angle)
            points.extend([x, y])

        return points

    def _blend_colors(self, color1: str, color2: str, ratio: float) -> str:
        """Blend two hex colors."""
        # Simple color blending - in a real implementation, use proper color space
        return color1  # Simplified for now

    def _animate(self):
        """Animate the widget."""
        if not self.visible:
            return

        self.animation_frame += 1

        # Update glow intensity with sine wave
        self.glow_intensity = (
            math.sin(self.animation_frame * self.theme.ANIMATION["glow_speed"]) + 1
        ) / 2

        # Update pulse phase
        self.pulse_phase += self.theme.ANIMATION["pulse_speed"]

        # Apply animations
        self._update_glow()
        self._update_pulse()

        # Schedule next frame
        self.canvas.after(16, self._animate)  # ~60 FPS

    def _update_glow(self):
        """Update glow effect."""
        # This would update the glow intensity of border elements
        pass

    def _update_pulse(self):
        """Update pulse effect."""
        # This would update the pulse animation
        pass

    def update_data(self, new_data: Dict):
        """Update widget data."""
        self.data = new_data
        self._refresh_content()

    def _refresh_content(self):
        """Refresh widget content display."""
        # Override in subclasses
        pass

    def destroy(self):
        """Destroy the widget."""
        for element in self.elements:
            self.canvas.delete(element)
        self.elements.clear()


class SystemStatusWidget(AnimatedWidget):
    """System status monitoring widget."""

    def _create_content(self, style: Dict):
        """Create system status content."""
        super()._create_content(style)

        # CPU usage arc
        self.cpu_arc = self.canvas.create_arc(
            self.x - 40,
            self.y - 40,
            self.x + 40,
            self.y + 40,
            start=90,
            extent=0,
            outline=self.theme.COLORS["accent_cyan"],
            width=3,
            style="arc",
        )

        # Memory usage arc
        self.memory_arc = self.canvas.create_arc(
            self.x - 30,
            self.y - 30,
            self.x + 30,
            self.y + 30,
            start=90,
            extent=0,
            outline=self.theme.COLORS["accent_blue"],
            width=3,
            style="arc",
        )

        # Status text
        self.status_text = self.canvas.create_text(
            self.x,
            self.y,
            text="SYSTEM\nONLINE",
            fill=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["small"],
            anchor="center",
            justify="center",
        )

        self.elements.extend([self.cpu_arc, self.memory_arc, self.status_text])

    def _refresh_content(self):
        """Refresh system status display."""
        cpu_percent = self.data.get("cpu_percent", 0)
        memory_percent = self.data.get("memory_percent", 0)

        # Update CPU arc
        cpu_extent = -int(cpu_percent * 3.6)  # Convert to degrees
        self.canvas.itemconfig(self.cpu_arc, extent=cpu_extent)

        # Update memory arc
        memory_extent = -int(memory_percent * 3.6)
        self.canvas.itemconfig(self.memory_arc, extent=memory_extent)

        # Update status text
        status = "SYSTEM\nONLINE" if cpu_percent < 90 else "SYSTEM\nSTRAIN"
        color = (
            self.theme.COLORS["success"]
            if cpu_percent < 90
            else self.theme.COLORS["warning"]
        )

        self.canvas.itemconfig(self.status_text, text=status, fill=color)


class NetworkStatusWidget(AnimatedWidget):
    """Network status and activity widget."""

    def _create_content(self, style: Dict):
        """Create network status content."""
        super()._create_content(style)

        # Network nodes
        self.nodes = []
        for i in range(6):
            angle = i * math.pi / 3
            x = self.x + 25 * math.cos(angle)
            y = self.y + 25 * math.sin(angle)

            node = self.canvas.create_oval(
                x - 3,
                y - 3,
                x + 3,
                y + 3,
                fill=self.theme.COLORS["accent_cyan"],
                outline="",
            )
            self.nodes.append(node)

        # Center node
        self.center_node = self.canvas.create_oval(
            self.x - 5,
            self.y - 5,
            self.x + 5,
            self.y + 5,
            fill=self.theme.COLORS["accent_white"],
            outline="",
        )

        # Connection lines
        self.connections = []
        for node in self.nodes:
            coords = self.canvas.coords(node)
            node_x, node_y = (coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2

            line = self.canvas.create_line(
                self.x,
                self.y,
                node_x,
                node_y,
                fill=self.theme.COLORS["accent_blue"],
                width=1,
            )
            self.connections.append(line)

        self.elements.extend(self.nodes + [self.center_node] + self.connections)

    def _update_pulse(self):
        """Update network pulse animation."""
        # Animate connection lines
        for i, line in enumerate(self.connections):
            phase = self.pulse_phase + i * math.pi / 3
            alpha = (math.sin(phase) + 1) / 2
            # In a real implementation, this would update line opacity

    def _refresh_content(self):
        """Refresh network status display."""
        connected = self.data.get("connected", True)
        color = (
            self.theme.COLORS["success"] if connected else self.theme.COLORS["error"]
        )

        self.canvas.itemconfig(self.center_node, fill=color)


class AgentStatusWidget(AnimatedWidget):
    """Agent status and activity widget."""

    def _create_content(self, style: Dict):
        """Create agent status content."""
        super()._create_content(style)

        # Agent count display
        self.agent_count_text = self.canvas.create_text(
            self.x,
            self.y - 10,
            text="0",
            fill=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["large"],
            anchor="center",
        )

        # Agent label
        self.agent_label = self.canvas.create_text(
            self.x,
            self.y + 15,
            text="AGENTS",
            fill=self.theme.COLORS["text_secondary"],
            font=self.theme.FONTS["small"],
            anchor="center",
        )

        # Activity indicators
        self.activity_dots = []
        for i in range(8):
            angle = i * math.pi / 4
            x = self.x + 35 * math.cos(angle)
            y = self.y + 35 * math.sin(angle)

            dot = self.canvas.create_oval(
                x - 2,
                y - 2,
                x + 2,
                y + 2,
                fill=self.theme.COLORS["text_dim"],
                outline="",
            )
            self.activity_dots.append(dot)

        self.elements.extend(
            [self.agent_count_text, self.agent_label] + self.activity_dots
        )

    def _refresh_content(self):
        """Refresh agent status display."""
        agent_count = self.data.get("agent_count", 0)
        active_agents = self.data.get("active_agents", 0)

        self.canvas.itemconfig(self.agent_count_text, text=str(agent_count))

        # Update activity dots
        for i, dot in enumerate(self.activity_dots):
            color = (
                self.theme.COLORS["accent_cyan"]
                if i < active_agents
                else self.theme.COLORS["text_dim"]
            )
            self.canvas.itemconfig(dot, fill=color)


class SecurityStatusWidget(AnimatedWidget):
    """Security status monitoring widget."""

    def _create_content(self, style: Dict):
        """Create security status content."""
        super()._create_content(style)

        # Security shield
        shield_points = [
            self.x,
            self.y - 30,  # Top
            self.x - 20,
            self.y - 10,  # Top left
            self.x - 20,
            self.y + 10,  # Bottom left
            self.x,
            self.y + 30,  # Bottom
            self.x + 20,
            self.y + 10,  # Bottom right
            self.x + 20,
            self.y - 10,  # Top right
        ]

        self.shield = self.canvas.create_polygon(
            shield_points, fill="", outline=self.theme.COLORS["accent_cyan"], width=2
        )

        # Security level text
        self.security_text = self.canvas.create_text(
            self.x,
            self.y,
            text="SECURE",
            fill=self.theme.COLORS["success"],
            font=self.theme.FONTS["small"],
            anchor="center",
        )

        self.elements.extend([self.shield, self.security_text])

    def _refresh_content(self):
        """Refresh security status display."""
        threat_level = self.data.get("threat_level", "low")

        if threat_level == "low":
            color = self.theme.COLORS["success"]
            text = "SECURE"
        elif threat_level == "medium":
            color = self.theme.COLORS["warning"]
            text = "CAUTION"
        else:
            color = self.theme.COLORS["error"]
            text = "THREAT"

        self.canvas.itemconfig(self.shield, outline=color)
        self.canvas.itemconfig(self.security_text, text=text, fill=color)


class CyberDashboard:
    """Main cyber dashboard interface."""

    def __init__(self, config: Dict = None):
        """Initialize the cyber dashboard."""
        self.config = config or self._default_config()
        self.theme = CyberTheme()
        self.widgets = {}
        self.particles = []
        self.grid_lines = []

        # Create main window
        self._create_window()

        # Create background effects
        self._create_background()

        # Create widgets
        self._create_widgets()

        # Start update loop
        self._start_update_loop()

    def _default_config(self) -> Dict:
        """Get default dashboard configuration."""
        return {
            "window": {
                "title": "WADE Cyber Dashboard",
                "fullscreen": True,
                "background": "#000000",
                "cursor": "none",
            },
            "grid": {
                "enabled": True,
                "spacing": 50,
                "color": "#002040",
                "animated": True,
            },
            "particles": {"enabled": True, "count": 50, "speed": 1, "color": "#0040ff"},
            "widgets": [
                {
                    "id": "system_status",
                    "type": "system",
                    "position": (200, 200),
                    "size": (120, 120),
                    "title": "SYSTEM STATUS",
                },
                {
                    "id": "network_status",
                    "type": "network",
                    "position": (400, 150),
                    "size": (100, 100),
                    "title": "NETWORK",
                },
                {
                    "id": "agent_status",
                    "type": "agents",
                    "position": (600, 250),
                    "size": (110, 110),
                    "title": "AGENTS",
                },
                {
                    "id": "security_status",
                    "type": "security",
                    "position": (300, 400),
                    "size": (90, 90),
                    "title": "SECURITY",
                },
            ],
        }

    def _create_window(self):
        """Create the main dashboard window."""
        self.root = tk.Tk()
        self.root.title(self.config["window"]["title"])
        self.root.configure(bg=self.config["window"]["background"])

        if self.config["window"]["fullscreen"]:
            self.root.attributes("-fullscreen", True)
            self.root.attributes("-topmost", True)

        if self.config["window"]["cursor"] == "none":
            self.root.configure(cursor="none")

        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Create main canvas
        self.canvas = Canvas(
            self.root,
            width=self.screen_width,
            height=self.screen_height,
            bg=self.theme.COLORS["bg_primary"],
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Bind events
        self.root.bind("<Escape>", self._on_escape)
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_mouse_move)

    def _create_background(self):
        """Create background effects."""
        if self.config["grid"]["enabled"]:
            self._create_grid()

        if self.config["particles"]["enabled"]:
            self._create_particles()

    def _create_grid(self):
        """Create animated grid background."""
        spacing = self.config["grid"]["spacing"]
        color = self.config["grid"]["color"]

        # Vertical lines
        for x in range(0, self.screen_width, spacing):
            line = self.canvas.create_line(
                x, 0, x, self.screen_height, fill=color, width=1
            )
            self.grid_lines.append(line)

        # Horizontal lines
        for y in range(0, self.screen_height, spacing):
            line = self.canvas.create_line(
                0, y, self.screen_width, y, fill=color, width=1
            )
            self.grid_lines.append(line)

    def _create_particles(self):
        """Create floating particles."""
        particle_count = self.config["particles"]["count"]
        color = self.config["particles"]["color"]

        for _ in range(particle_count):
            x = random.randint(0, self.screen_width)
            y = random.randint(0, self.screen_height)

            particle = {
                "element": self.canvas.create_oval(
                    x - 1, y - 1, x + 1, y + 1, fill=color, outline=""
                ),
                "x": x,
                "y": y,
                "vx": random.uniform(-1, 1),
                "vy": random.uniform(-1, 1),
                "life": random.uniform(0.5, 1.0),
            }
            self.particles.append(particle)

    def _create_widgets(self):
        """Create dashboard widgets."""
        for widget_config in self.config["widgets"]:
            config = WidgetConfig(**widget_config)

            if config.widget_type == "system":
                widget = SystemStatusWidget(self.canvas, config, self.theme)
            elif config.widget_type == "network":
                widget = NetworkStatusWidget(self.canvas, config, self.theme)
            elif config.widget_type == "agents":
                widget = AgentStatusWidget(self.canvas, config, self.theme)
            elif config.widget_type == "security":
                widget = SecurityStatusWidget(self.canvas, config, self.theme)
            else:
                widget = AnimatedWidget(self.canvas, config, self.theme)

            self.widgets[config.widget_id] = widget

    def _start_update_loop(self):
        """Start the main update loop."""
        self._update_background()
        self._update_widgets()

        # Schedule next update
        self.root.after(50, self._start_update_loop)  # 20 FPS for background

    def _update_background(self):
        """Update background animations."""
        if self.config["grid"]["animated"]:
            self._animate_grid()

        if self.config["particles"]["enabled"]:
            self._animate_particles()

    def _animate_grid(self):
        """Animate grid lines."""
        # Subtle grid animation - could pulse or shift
        pass

    def _animate_particles(self):
        """Animate floating particles."""
        speed = self.config["particles"]["speed"]

        for particle in self.particles:
            # Update position
            particle["x"] += particle["vx"] * speed
            particle["y"] += particle["vy"] * speed

            # Wrap around screen
            if particle["x"] < 0:
                particle["x"] = self.screen_width
            elif particle["x"] > self.screen_width:
                particle["x"] = 0

            if particle["y"] < 0:
                particle["y"] = self.screen_height
            elif particle["y"] > self.screen_height:
                particle["y"] = 0

            # Update visual position
            self.canvas.coords(
                particle["element"],
                particle["x"] - 1,
                particle["y"] - 1,
                particle["x"] + 1,
                particle["y"] + 1,
            )

            # Update life and fade
            particle["life"] -= 0.001
            if particle["life"] <= 0:
                particle["life"] = 1.0

    def _update_widgets(self):
        """Update widget data."""
        # This would integrate with actual system monitoring
        import psutil

        try:
            # System status data
            system_data = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
            }

            if "system_status" in self.widgets:
                self.widgets["system_status"].update_data(system_data)

            # Network status data
            network_data = {
                "connected": True,  # Would check actual network status
                "bandwidth_usage": 45,
            }

            if "network_status" in self.widgets:
                self.widgets["network_status"].update_data(network_data)

            # Agent status data
            agent_data = {"agent_count": 5, "active_agents": 3}

            if "agent_status" in self.widgets:
                self.widgets["agent_status"].update_data(agent_data)

            # Security status data
            security_data = {"threat_level": "low", "active_scans": 2}

            if "security_status" in self.widgets:
                self.widgets["security_status"].update_data(security_data)

        except Exception as e:
            print(f"Error updating widget data: {e}")

    def _on_escape(self, event):
        """Handle escape key press."""
        self.root.quit()

    def _toggle_fullscreen(self, event):
        """Toggle fullscreen mode."""
        current = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not current)

    def _on_click(self, event):
        """Handle mouse click."""
        # Could implement widget interaction
        pass

    def _on_mouse_move(self, event):
        """Handle mouse movement."""
        # Could implement hover effects
        pass

    def run(self):
        """Run the dashboard."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        """Shutdown the dashboard."""
        for widget in self.widgets.values():
            widget.destroy()

        self.root.quit()


def main():
    """Main entry point for the cyber dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="WADE Cyber Dashboard")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument(
        "--windowed", "-w", action="store_true", help="Run in windowed mode"
    )
    parser.add_argument(
        "--no-particles", action="store_true", help="Disable particle effects"
    )
    parser.add_argument(
        "--no-grid", action="store_true", help="Disable grid background"
    )

    args = parser.parse_args()

    # Load configuration
    config = None
    if args.config and os.path.exists(args.config):
        with open(args.config, "r") as f:
            config = json.load(f)

    # Create dashboard
    dashboard = CyberDashboard(config)

    # Apply command line options
    if args.windowed:
        dashboard.config["window"]["fullscreen"] = False
        dashboard.root.attributes("-fullscreen", False)

    if args.no_particles:
        dashboard.config["particles"]["enabled"] = False

    if args.no_grid:
        dashboard.config["grid"]["enabled"] = False

    # Run dashboard
    try:
        dashboard.run()
    except Exception as e:
        print(f"Dashboard error: {e}")
        dashboard.shutdown()


if __name__ == "__main__":
    main()
