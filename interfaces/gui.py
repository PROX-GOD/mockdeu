import asyncio
import threading
import time
import math
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Optional, Callable
from mockdeu.interfaces.base import InterviewInterface

# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM THEME CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class Theme:
    """Premium dark theme with government aesthetic"""
    
    # Primary Colors
    BG_PRIMARY = "#0d1117"          # Deep space black
    BG_SECONDARY = "#161b22"        # Elevated surface
    BG_TERTIARY = "#21262d"         # Card background
    
    # Accent Colors
    ACCENT_GOLD = "#d4af37"         # Official gold
    ACCENT_GOLD_DARK = "#b8962e"    # Pressed gold
    ACCENT_GOLD_GLOW = "#ffd700"    # Hover gold
    ACCENT_BLUE = "#58a6ff"         # Info blue
    ACCENT_RED = "#f85149"          # Alert red
    ACCENT_GREEN = "#3fb950"        # Success green
    
    # Text Colors
    TEXT_PRIMARY = "#f0f6fc"        # Bright white
    TEXT_SECONDARY = "#8b949e"      # Muted gray
    TEXT_TERTIARY = "#484f58"       # Subtle gray
    
    # Message Colors
    OFFICER_BG = "#1c2128"          # Officer message
    OFFICER_BORDER = "#30363d"
    APPLICANT_BG = "#0d2d0d"        # Applicant message
    APPLICANT_BORDER = "#238636"
    
    # Status Colors
    STATUS_LISTENING = "#3fb950"
    STATUS_PROCESSING = "#d4af37"
    STATUS_IDLE = "#8b949e"
    
    # Fonts (Modern + Professional)
    FONT_DISPLAY = ("Segoe UI", 28, "bold")
    FONT_HEADER = ("Segoe UI Semibold", 18)
    FONT_SUBHEADER = ("Segoe UI", 14, "bold")
    FONT_BODY = ("Segoe UI", 13)
    FONT_SMALL = ("Segoe UI", 11)
    FONT_MONO = ("Consolas", 13)
    FONT_LABEL = ("Segoe UI", 10)
    
    # Sizing
    CORNER_RADIUS = 12
    CORNER_RADIUS_SM = 8
    PADDING_XL = 30
    PADDING_LG = 20
    PADDING_MD = 15
    PADDING_SM = 10
    PADDING_XS = 5
    
    # Animation
    ANIM_SPEED_FAST = 16      # ms
    ANIM_SPEED_NORMAL = 25    # ms
    ANIM_SPEED_SLOW = 40      # ms
    TYPING_SPEED = 15         # ms per character


# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM ICONS (Unicode + Custom Drawing)
# ═══════════════════════════════════════════════════════════════════════════════

class Icons:
    """Unicode icons for consistent styling"""
    SEAL = "⚜"
    USER = "👤"
    PASSPORT = "📘"
    CASE = "📋"
    VISA = "🎫"
    MIC = "🎙"
    PROCESSING = "⚙"
    CHECK = "✓"
    CROSS = "✗"
    ARROW_RIGHT = "→"
    ARROW_LEFT = "←"
    BULLET = "•"
    STAR = "★"
    SHIELD = "🛡"
    LOCK = "🔒"
    CLOCK = "⏱"
    WAVE = "〰"
    DOT = "●"
    CIRCLE_EMPTY = "○"


# ═══════════════════════════════════════════════════════════════════════════════
# ANIMATED COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════════

class PulsingDot(ctk.CTkCanvas):
    """Animated status indicator with smooth pulsing"""
    
    def __init__(self, master, size=16, color=Theme.STATUS_IDLE, **kwargs):
        super().__init__(
            master, 
            width=size + 10, 
            height=size + 10, 
            bg=Theme.BG_SECONDARY, 
            highlightthickness=0,
            **kwargs
        )
        self.size = size
        self.base_color = color
        self.current_color = color
        self.is_pulsing = False
        self.pulse_step = 0
        self.center = (size + 10) // 2
        
        # Draw initial dot
        self._draw_dot(size)
    
    def _draw_dot(self, size, glow=False):
        self.delete("all")
        offset = (self.size + 10 - size) // 2
        
        # Glow effect
        if glow:
            for i in range(3):
                glow_size = size + (3-i) * 4
                glow_offset = (self.size + 10 - glow_size) // 2
                alpha = 0.1 + i * 0.1
                self.create_oval(
                    glow_offset, glow_offset,
                    glow_offset + glow_size, glow_offset + glow_size,
                    fill=self._adjust_alpha(self.current_color, alpha),
                    outline=""
                )
        
        # Main dot
        self.create_oval(
            offset, offset,
            offset + size, offset + size,
            fill=self.current_color,
            outline=""
        )
    
    def _adjust_alpha(self, color, alpha):
        """Create a darker version for pseudo-alpha"""
        # Simple darkening for glow effect
        return color
    
    def set_color(self, color):
        self.current_color = color
        self.base_color = color
        self._draw_dot(self.size)
    
    def start_pulse(self, color=None):
        if color:
            self.current_color = color
        self.is_pulsing = True
        self._animate_pulse()
    
    def stop_pulse(self):
        self.is_pulsing = False
        self._draw_dot(self.size)
    
    def _animate_pulse(self):
        if not self.is_pulsing:
            return
        
        # Smooth sine wave animation
        scale = 0.3 * math.sin(self.pulse_step * 0.15) + 1.0
        current_size = int(self.size * scale)
        
        self._draw_dot(current_size, glow=True)
        
        self.pulse_step += 1
        self.after(50, self._animate_pulse)


class WaveformVisualizer(ctk.CTkCanvas):
    """Audio waveform visualizer for listening state"""
    
    def __init__(self, master, width=120, height=40, **kwargs):
        super().__init__(
            master,
            width=width,
            height=height,
            bg=Theme.BG_SECONDARY,
            highlightthickness=0,
            **kwargs
        )
        self.bar_count = 12
        self.bars = []
        self.is_active = False
        self.animation_step = 0
        self.width = width
        self.height = height
        
        self._create_bars()
    
    def _create_bars(self):
        bar_width = 4
        gap = (self.width - self.bar_count * bar_width) // (self.bar_count + 1)
        
        for i in range(self.bar_count):
            x = gap + i * (bar_width + gap)
            bar = self.create_rectangle(
                x, self.height // 2 - 2,
                x + bar_width, self.height // 2 + 2,
                fill=Theme.STATUS_IDLE,
                outline=""
            )
            self.bars.append(bar)
    
    def start(self):
        self.is_active = True
        self._animate()
    
    def stop(self):
        self.is_active = False
        # Reset bars to idle
        for i, bar in enumerate(self.bars):
            bar_width = 4
            gap = (self.width - self.bar_count * bar_width) // (self.bar_count + 1)
            x = gap + i * (bar_width + gap)
            self.coords(bar, x, self.height // 2 - 2, x + bar_width, self.height // 2 + 2)
            self.itemconfig(bar, fill=Theme.STATUS_IDLE)
    
    def _animate(self):
        if not self.is_active:
            return
        
        bar_width = 4
        gap = (self.width - self.bar_count * bar_width) // (self.bar_count + 1)
        
        for i, bar in enumerate(self.bars):
            # Create wave pattern
            phase = self.animation_step * 0.2 + i * 0.5
            amplitude = 8 + 6 * math.sin(phase)
            
            x = gap + i * (bar_width + gap)
            y_center = self.height // 2
            
            self.coords(
                bar,
                x, y_center - amplitude,
                x + bar_width, y_center + amplitude
            )
            self.itemconfig(bar, fill=Theme.STATUS_LISTENING)
        
        self.animation_step += 1
        self.after(50, self._animate)


class TypewriterLabel(ctk.CTkLabel):
    """Label with typewriter animation effect"""
    
    def __init__(self, master, text="", speed=Theme.TYPING_SPEED, on_complete=None, **kwargs):
        super().__init__(master, text="", **kwargs)
        self.full_text = text
        self.speed = speed
        self.on_complete = on_complete
        self.current_index = 0
        self.is_typing = False
    
    def start_typing(self, text=None):
        if text:
            self.full_text = text
        self.current_index = 0
        self.is_typing = True
        self._type_next()
    
    def _type_next(self):
        if not self.is_typing:
            return
        
        if self.current_index <= len(self.full_text):
            display_text = self.full_text[:self.current_index]
            cursor = "█" if self.current_index < len(self.full_text) else ""
            self.configure(text=display_text + cursor)
            self.current_index += 1
            self.after(self.speed, self._type_next)
        else:
            self.configure(text=self.full_text)
            self.is_typing = False
            if self.on_complete:
                self.on_complete()
    
    def skip_animation(self):
        self.is_typing = False
        self.configure(text=self.full_text)


# ═══════════════════════════════════════════════════════════════════════════════
# ENHANCED CHAT BUBBLE
# ═══════════════════════════════════════════════════════════════════════════════

class ChatBubble(ctk.CTkFrame):
    """Premium chat bubble with sender avatar and styling"""
    
    def __init__(self, master, text, sender, animated=False, **kwargs):
        self.sender = sender
        self.is_officer = sender == "Officer"
        
        # Colors based on sender
        bg_color = Theme.OFFICER_BG if self.is_officer else Theme.APPLICANT_BG
        border_color = Theme.OFFICER_BORDER if self.is_officer else Theme.APPLICANT_BORDER
        
        super().__init__(
            master, 
            fg_color=bg_color, 
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1,
            border_color=border_color,
            **kwargs
        )
        
        # Inner container
        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Header with icon and name
        self.header = ctk.CTkFrame(self.inner, fg_color="transparent")
        self.header.pack(fill="x", padx=Theme.PADDING_SM, pady=(Theme.PADDING_SM, 0))
        
        # Sender icon
        icon = Icons.SHIELD if self.is_officer else Icons.USER
        icon_color = Theme.ACCENT_GOLD if self.is_officer else Theme.ACCENT_GREEN
        
        self.icon_label = ctk.CTkLabel(
            self.header,
            text=icon,
            font=("Segoe UI Emoji", 14),
            text_color=icon_color
        )
        self.icon_label.pack(side="left", padx=(0, 5))
        
        # Sender name
        self.name_label = ctk.CTkLabel(
            self.header,
            text="CONSULAR OFFICER" if self.is_officer else "APPLICANT",
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_SECONDARY
        )
        self.name_label.pack(side="left")
        
        # Timestamp (optional)
        self.time_label = ctk.CTkLabel(
            self.header,
            text=time.strftime("%H:%M"),
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_TERTIARY
        )
        self.time_label.pack(side="right")
        
        # Message text
        if animated and self.is_officer:
            self.text_label = TypewriterLabel(
                self.inner,
                text=text,
                wraplength=480,
                justify="left",
                anchor="w",
                text_color=Theme.TEXT_PRIMARY,
                font=Theme.FONT_BODY
            )
            self.text_label.pack(
                fill="x", 
                padx=Theme.PADDING_MD, 
                pady=(Theme.PADDING_XS, Theme.PADDING_MD)
            )
            self.text_label.start_typing()
        else:
            self.text_label = ctk.CTkLabel(
                self.inner,
                text=text,
                wraplength=480,
                justify="left",
                anchor="w",
                text_color=Theme.TEXT_PRIMARY,
                font=Theme.FONT_BODY
            )
            self.text_label.pack(
                fill="x", 
                padx=Theme.PADDING_MD, 
                pady=(Theme.PADDING_XS, Theme.PADDING_MD)
            )
    
    def update_text(self, text):
        self.text_label.configure(text=text)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR CARD COMPONENT
# ═══════════════════════════════════════════════════════════════════════════════

class InfoCard(ctk.CTkFrame):
    """Stylized information card for sidebar"""
    
    def __init__(self, master, icon, label, value, **kwargs):
        super().__init__(
            master,
            fg_color=Theme.BG_TERTIARY,
            corner_radius=Theme.CORNER_RADIUS_SM,
            **kwargs
        )
        
        # Icon
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon,
            font=("Segoe UI Emoji", 16),
            text_color=Theme.ACCENT_GOLD
        )
        self.icon_label.pack(anchor="w", padx=Theme.PADDING_SM, pady=(Theme.PADDING_SM, 0))
        
        # Label
        self.label = ctk.CTkLabel(
            self,
            text=label,
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_TERTIARY
        )
        self.label.pack(anchor="w", padx=Theme.PADDING_SM, pady=(2, 0))
        
        # Value
        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=Theme.FONT_MONO,
            text_color=Theme.TEXT_PRIMARY
        )
        self.value_label.pack(anchor="w", padx=Theme.PADDING_SM, pady=(0, Theme.PADDING_SM))
    
    def set_value(self, value):
        self.value_label.configure(text=value)


# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM INPUT DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class PremiumInputDialog(ctk.CTkToplevel):
    """Custom styled input dialog"""
    
    def __init__(self, parent, title="Input Required", prompt="", options=None):
        super().__init__(parent)
        
        self.title(title)
        self.geometry("500x280")
        self.configure(fg_color=Theme.BG_PRIMARY)
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        self.options = options
        
        # Main container with padding
        self.container = ctk.CTkFrame(self, fg_color=Theme.BG_SECONDARY, corner_radius=Theme.CORNER_RADIUS)
        self.container.pack(fill="both", expand=True, padx=Theme.PADDING_MD, pady=Theme.PADDING_MD)
        
        # Header
        self.header = ctk.CTkFrame(self.container, fg_color="transparent")
        self.header.pack(fill="x", padx=Theme.PADDING_LG, pady=(Theme.PADDING_LG, Theme.PADDING_SM))
        
        ctk.CTkLabel(
            self.header,
            text=f"{Icons.MIC} RESPONSE REQUIRED",
            font=Theme.FONT_SUBHEADER,
            text_color=Theme.ACCENT_GOLD
        ).pack(anchor="w")
        
        # Prompt
        ctk.CTkLabel(
            self.container,
            text=prompt,
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            wraplength=420
        ).pack(fill="x", padx=Theme.PADDING_LG, pady=Theme.PADDING_SM)
        
        # Input or Options
        if options:
            self.option_var = ctk.StringVar(value=options[0] if options else "")
            self.input_widget = ctk.CTkOptionMenu(
                self.container,
                variable=self.option_var,
                values=options,
                font=Theme.FONT_BODY,
                fg_color=Theme.BG_TERTIARY,
                button_color=Theme.ACCENT_GOLD,
                button_hover_color=Theme.ACCENT_GOLD_GLOW,
                dropdown_fg_color=Theme.BG_TERTIARY,
                dropdown_hover_color=Theme.BG_SECONDARY,
                corner_radius=Theme.CORNER_RADIUS_SM
            )
        else:
            self.input_widget = ctk.CTkEntry(
                self.container,
                font=Theme.FONT_BODY,
                fg_color=Theme.BG_TERTIARY,
                border_color=Theme.ACCENT_GOLD,
                text_color=Theme.TEXT_PRIMARY,
                placeholder_text="Type your response...",
                corner_radius=Theme.CORNER_RADIUS_SM,
                height=40
            )
            self.input_widget.bind("<Return>", lambda e: self._submit())
        
        self.input_widget.pack(fill="x", padx=Theme.PADDING_LG, pady=Theme.PADDING_SM)
        
        # Buttons
        self.btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=Theme.PADDING_LG, pady=Theme.PADDING_LG)
        
        self.submit_btn = ctk.CTkButton(
            self.btn_frame,
            text=f"SUBMIT {Icons.ARROW_RIGHT}",
            font=Theme.FONT_BODY,
            fg_color=Theme.ACCENT_GOLD,
            hover_color=Theme.ACCENT_GOLD_GLOW,
            text_color=Theme.BG_PRIMARY,
            corner_radius=Theme.CORNER_RADIUS_SM,
            height=40,
            command=self._submit
        )
        self.submit_btn.pack(side="right")
        
        self.cancel_btn = ctk.CTkButton(
            self.btn_frame,
            text="CANCEL",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            hover_color=Theme.BG_TERTIARY,
            text_color=Theme.TEXT_SECONDARY,
            border_width=1,
            border_color=Theme.TEXT_TERTIARY,
            corner_radius=Theme.CORNER_RADIUS_SM,
            height=40,
            command=self._cancel
        )
        self.cancel_btn.pack(side="right", padx=(0, Theme.PADDING_SM))
        
        # Focus input
        self.after(100, lambda: self.input_widget.focus_set())
    
    def _submit(self):
        if hasattr(self, 'option_var'):
            self.result = self.option_var.get()
        else:
            self.result = self.input_widget.get()
        self.destroy()
    
    def _cancel(self):
        self.result = None
        self.destroy()
    
    def get_input(self):
        self.wait_window()
        return self.result


# ═══════════════════════════════════════════════════════════════════════════════
# FEEDBACK REPORT DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

class FeedbackReportDialog(ctk.CTkToplevel):
    """Premium feedback report display"""
    
    def __init__(self, parent, content):
        super().__init__(parent)
        
        self.title("OFFICIAL FEEDBACK REPORT")
        self.geometry("800x700")
        self.configure(fg_color=Theme.BG_PRIMARY)
        
        # Header
        self.header = ctk.CTkFrame(self, fg_color=Theme.BG_SECONDARY, height=80)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)
        
        header_inner = ctk.CTkFrame(self.header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=Theme.PADDING_XL, pady=Theme.PADDING_MD)
        
        # Classification badge
        badge_frame = ctk.CTkFrame(header_inner, fg_color=Theme.ACCENT_RED, corner_radius=4)
        badge_frame.pack(anchor="w")
        
        ctk.CTkLabel(
            badge_frame,
            text=" CONFIDENTIAL ",
            font=("Segoe UI", 10, "bold"),
            text_color="white"
        ).pack(padx=5, pady=2)
        
        ctk.CTkLabel(
            header_inner,
            text="INTERVIEW ASSESSMENT REPORT",
            font=Theme.FONT_DISPLAY,
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w", pady=(5, 0))
        
        # Content
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=Theme.PADDING_XL, pady=Theme.PADDING_LG)
        
        self.textbox = ctk.CTkTextbox(
            self.content_frame,
            fg_color=Theme.BG_SECONDARY,
            text_color=Theme.TEXT_PRIMARY,
            font=Theme.FONT_BODY,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1,
            border_color=Theme.BG_TERTIARY
        )
        self.textbox.pack(fill="both", expand=True)
        self.textbox.insert("0.0", content)
        self.textbox.configure(state="disabled")
        
        # Footer
        self.footer = ctk.CTkFrame(self, fg_color="transparent", height=60)
        self.footer.pack(fill="x", padx=Theme.PADDING_XL, pady=Theme.PADDING_MD)
        
        ctk.CTkButton(
            self.footer,
            text="CLOSE REPORT",
            font=Theme.FONT_BODY,
            fg_color=Theme.ACCENT_GOLD,
            hover_color=Theme.ACCENT_GOLD_GLOW,
            text_color=Theme.BG_PRIMARY,
            corner_radius=Theme.CORNER_RADIUS_SM,
            height=40,
            command=self.destroy
        ).pack(side="right")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN GUI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

class GUIInterface(InterviewInterface):
    """Premium GUI interface for MockDeu visa interview simulator"""
    
    def __init__(self):
        self.root = None
        self.chat_frame = None
        self.status_label = None
        self.waveform = None
        self.status_dot = None
        self.loop = None
        self.running = False
        self.case_details = {}
        self.info_cards = {}
        self.message_count = 0
    
    async def initialize(self) -> bool:
        self.loop = asyncio.get_running_loop()
        self.running = True
        
        self.gui_thread = threading.Thread(target=self._run_gui, daemon=True)
        self.gui_thread.start()
        
        # Wait for GUI to initialize
        while self.root is None:
            await asyncio.sleep(0.1)
        
        return True
    
    def _run_gui(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        self.root = ctk.CTk()
        self.root.title("MockDeu — Official Visa Interview Simulator")
        self.root.geometry("1200x850")
        self.root.minsize(1000, 700)
        self.root.configure(fg_color=Theme.BG_PRIMARY)
        
        # Configure grid
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        self._create_sidebar()
        self._create_main_area()
        self._create_status_bar()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
    
    def _create_sidebar(self):
        """Create premium sidebar with seal and case details"""
        self.sidebar = ctk.CTkFrame(
            self.root, 
            width=280, 
            corner_radius=0, 
            fg_color=Theme.BG_SECONDARY
        )
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # === Logo / Seal Area ===
        seal_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        seal_frame.pack(fill="x", pady=(Theme.PADDING_XL, Theme.PADDING_MD))
        
        # Gold accent line
        ctk.CTkFrame(
            seal_frame, 
            height=3, 
            fg_color=Theme.ACCENT_GOLD
        ).pack(fill="x", padx=Theme.PADDING_XL)
        
        # Seal container with border
        seal_container = ctk.CTkFrame(
            seal_frame,
            fg_color=Theme.BG_TERTIARY,
            corner_radius=Theme.CORNER_RADIUS
        )
        seal_container.pack(padx=Theme.PADDING_LG, pady=Theme.PADDING_MD)
        
        # Large seal icon
        ctk.CTkLabel(
            seal_container,
            text="🦅",
            font=("Segoe UI Emoji", 48),
            text_color=Theme.ACCENT_GOLD
        ).pack(pady=(Theme.PADDING_MD, 5))
        
        # Department text
        ctk.CTkLabel(
            seal_container,
            text="UNITED STATES",
            font=("Segoe UI", 12, "bold"),
            text_color=Theme.ACCENT_GOLD
        ).pack()
        
        ctk.CTkLabel(
            seal_container,
            text="DEPARTMENT OF STATE",
            font=("Segoe UI", 10),
            text_color=Theme.TEXT_SECONDARY
        ).pack(pady=(0, Theme.PADDING_MD))
        
        # Gold accent line
        ctk.CTkFrame(
            seal_frame, 
            height=3, 
            fg_color=Theme.ACCENT_GOLD
        ).pack(fill="x", padx=Theme.PADDING_XL)
        
        # === Section Header ===
        section_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        section_header.pack(fill="x", padx=Theme.PADDING_LG, pady=(Theme.PADDING_LG, Theme.PADDING_SM))
        
        ctk.CTkLabel(
            section_header,
            text=f"{Icons.CASE} CASE FILE",
            font=Theme.FONT_SUBHEADER,
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")
        
        # === Case Details Container ===
        self.details_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.details_frame.pack(fill="x", padx=Theme.PADDING_LG, pady=Theme.PADDING_SM)
        
        # Placeholder cards
        self._create_info_cards()
        
        # === Bottom branding ===
        self.sidebar.pack_propagate(True)
        
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", pady=Theme.PADDING_LG)
        
        ctk.CTkLabel(
            bottom_frame,
            text="MockDeu v2.0",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_TERTIARY
        ).pack()
        
        ctk.CTkLabel(
            bottom_frame,
            text="OFFICIAL TRAINING SIMULATOR",
            font=("Segoe UI", 8),
            text_color=Theme.TEXT_TERTIARY
        ).pack()
    
    def _create_info_cards(self):
        """Create information cards for case details"""
        card_data = [
            ("applicant", Icons.USER, "APPLICANT", "—"),
            ("visa_type", Icons.VISA, "VISA CLASS", "—"),
            ("passport", Icons.PASSPORT, "PASSPORT NO.", "—"),
            ("case_id", Icons.CASE, "CASE ID", "—"),
        ]
        
        for key, icon, label, default in card_data:
            card = InfoCard(self.details_frame, icon, label, default)
            card.pack(fill="x", pady=(0, Theme.PADDING_SM))
            self.info_cards[key] = card
    
    def _create_main_area(self):
        """Create main chat area with header"""
        self.main_area = ctk.CTkFrame(self.root, fg_color=Theme.BG_PRIMARY)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        
        # === Header ===
        self.header = ctk.CTkFrame(
            self.main_area, 
            height=70, 
            fg_color=Theme.BG_SECONDARY,
            corner_radius=0
        )
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)
        
        header_inner = ctk.CTkFrame(self.header, fg_color="transparent")
        header_inner.pack(fill="both", expand=True, padx=Theme.PADDING_XL, pady=Theme.PADDING_MD)
        
        # Left side - title
        title_frame = ctk.CTkFrame(header_inner, fg_color="transparent")
        title_frame.pack(side="left", fill="y")
        
        ctk.CTkLabel(
            title_frame,
            text="OFFICIAL INTERVIEW RECORD",
            font=Theme.FONT_HEADER,
            text_color=Theme.TEXT_PRIMARY
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="Consular Section • Nonimmigrant Visa Unit",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        ).pack(anchor="w")
        
        # Right side - session info
        session_frame = ctk.CTkFrame(header_inner, fg_color=Theme.BG_TERTIARY, corner_radius=Theme.CORNER_RADIUS_SM)
        session_frame.pack(side="right", padx=Theme.PADDING_SM)
        
        ctk.CTkLabel(
            session_frame,
            text=f"{Icons.CLOCK} SESSION: {time.strftime('%Y-%m-%d %H:%M')}",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY
        ).pack(padx=Theme.PADDING_SM, pady=Theme.PADDING_XS)
        
        # === Chat Area ===
        chat_container = ctk.CTkFrame(self.main_area, fg_color="transparent")
        chat_container.grid(row=1, column=0, sticky="nsew", padx=Theme.PADDING_LG, pady=Theme.PADDING_MD)
        chat_container.grid_rowconfigure(0, weight=1)
        chat_container.grid_columnconfigure(0, weight=1)
        
        self.chat_frame = ctk.CTkScrollableFrame(
            chat_container,
            fg_color=Theme.BG_PRIMARY,
            corner_radius=Theme.CORNER_RADIUS,
            border_width=1,
            border_color=Theme.BG_TERTIARY
        )
        self.chat_frame.grid(row=0, column=0, sticky="nsew")
        
        # Welcome message
        self._add_system_message("Interview session initialized. The consular officer will begin shortly.")
    
    def _create_status_bar(self):
        """Create status bar with indicators"""
        self.status_bar = ctk.CTkFrame(
            self.root, 
            height=70, 
            fg_color=Theme.BG_SECONDARY,
            corner_radius=0
        )
        self.status_bar.grid(row=1, column=1, sticky="ew")
        self.status_bar.grid_propagate(False)
        
        inner = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=Theme.PADDING_XL, pady=Theme.PADDING_MD)
        
        # Left side - status
        status_left = ctk.CTkFrame(inner, fg_color="transparent")
        status_left.pack(side="left", fill="y")
        
        # Status dot
        self.status_dot = PulsingDot(status_left, size=12, color=Theme.STATUS_IDLE)
        self.status_dot.pack(side="left", padx=(0, Theme.PADDING_SM))
        
        self.status_label = ctk.CTkLabel(
            status_left,
            text="INITIALIZING SYSTEM...",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY
        )
        self.status_label.pack(side="left")
        
        # Right side - waveform visualizer
        status_right = ctk.CTkFrame(inner, fg_color="transparent")
        status_right.pack(side="right", fill="y")
        
        self.waveform = WaveformVisualizer(status_right)
        self.waveform.pack(side="right")
        
        waveform_label = ctk.CTkLabel(
            status_right,
            text="AUDIO INPUT",
            font=Theme.FONT_LABEL,
            text_color=Theme.TEXT_TERTIARY
        )
        waveform_label.pack(side="right", padx=(0, Theme.PADDING_SM))
    
    def _add_system_message(self, text):
        """Add a system notification message"""
        frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        frame.pack(fill="x", pady=Theme.PADDING_SM)
        
        inner = ctk.CTkFrame(frame, fg_color=Theme.BG_TERTIARY, corner_radius=Theme.CORNER_RADIUS_SM)
        inner.pack()
        
        ctk.CTkLabel(
            inner,
            text=f"{Icons.BULLET} {text}",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_TERTIARY
        ).pack(padx=Theme.PADDING_MD, pady=Theme.PADDING_XS)
    
    def _on_close(self):
        self.running = False
        self.root.destroy()
    
    async def set_case_details(self, details: dict):
        self.case_details = details
        if not self.running:
            return
        self.root.after(0, self._update_sidebar)
    
    def _update_sidebar(self):
        """Update sidebar with case details"""
        mappings = {
            "applicant": ("name", "Unknown"),
            "visa_type": ("visa_type", "N/A"),
            "passport": ("passport", "N/A"),
            "case_id": ("case_id", "N/A"),
        }
        
        for card_key, (detail_key, default) in mappings.items():
            if card_key in self.info_cards:
                value = self.case_details.get(detail_key, default)
                self.info_cards[card_key].set_value(str(value).upper())
    
    async def display_officer(self, text: str):
        if not self.running:
            return
        self.root.after(0, lambda: self._add_message("Officer", text, animated=True))
    
    async def display_applicant(self, text: str):
        if not self.running:
            return
        self.root.after(0, lambda: self._add_message("Applicant", text, animated=False))
    
    def _add_message(self, sender, text, animated=False):
        self.message_count += 1
        
        bubble = ChatBubble(self.chat_frame, text, sender, animated=animated)
        
        if sender == "Applicant":
            bubble.pack(
                fill="x",
                pady=Theme.PADDING_SM, 
                padx=(80, Theme.PADDING_SM), 
                anchor="e"
            )
        else:
            bubble.pack(
                fill="x",
                pady=Theme.PADDING_SM, 
                padx=(Theme.PADDING_SM, 80), 
                anchor="w"
            )
        
        # Scroll to bottom
        self._scroll_to_bottom()
    
    def _scroll_to_bottom(self):
        """Scroll chat to bottom"""
        self.chat_frame._parent_canvas.yview_moveto(1.0)
    
    async def update_status(self, text: str):
        if not self.running:
            return
        
        def _update():
            self.status_label.configure(text=text.upper())
            
            # Update indicators based on status
            status_lower = text.lower()
            
            if "listening" in status_lower:
                self.status_dot.set_color(Theme.STATUS_LISTENING)
                self.status_dot.start_pulse(Theme.STATUS_LISTENING)
                self.waveform.start()
            elif "processing" in status_lower or "thinking" in status_lower:
                self.status_dot.set_color(Theme.STATUS_PROCESSING)
                self.status_dot.start_pulse(Theme.STATUS_PROCESSING)
                self.waveform.stop()
            else:
                self.status_dot.stop_pulse()
                self.status_dot.set_color(Theme.STATUS_IDLE)
                self.waveform.stop()
        
        self.root.after(0, _update)
    
    async def get_input(self, prompt: str = "", options: list = None) -> str:
        if not self.running:
            return ""
        
        result = [None]
        done = threading.Event()
        
        def _ask():
            dialog = PremiumInputDialog(
                self.root,
                title="Response Required",
                prompt=prompt,
                options=options
            )
            result[0] = dialog.get_input()
            done.set()
        
        self.root.after(0, _ask)
        
        while not done.is_set():
            if not self.running:
                return ""
            await asyncio.sleep(0.1)
        
        return result[0] if result[0] else ""
    
    async def show_feedback(self, markdown_text: str):
        if not self.running:
            return
        
        def _show():
            FeedbackReportDialog(self.root, markdown_text)
        
        self.root.after(0, _show)
    
    def close(self):
        self.running = False
        if self.root:
            self.root.quit()
