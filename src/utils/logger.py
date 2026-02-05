"""
Logger - Rich console logging for LeadSniper.

This module provides a beautiful, colored terminal output using the Rich library.
Different colors are used for different types of operations to give the developer
a clear visual "heartbeat" of the system.
"""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text


# Custom theme for LeadSniper
LEADSNIPER_THEME = Theme({
    "info": "bold white",
    "scraping": "bold cyan",
    "email": "bold green",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "timestamp": "dim white",
    "domain": "bold blue",
    "status": "bold magenta",
})


class Logger:
    """
    Custom logger with colored output for LeadSniper operations.
    
    Uses Rich library for beautiful terminal output with color coding:
    - Cyan: Scraping operations
    - Green: Email operations (sent successfully)
    - Yellow: Warnings
    - Red: Errors
    - Blue: Domain references
    - Magenta: Status changes
    """

    def __init__(self) -> None:
        """Initialize the logger with custom theme."""
        self.console = Console(theme=LEADSNIPER_THEME)

    def _get_timestamp(self) -> str:
        """Get current timestamp formatted for logging."""
        return datetime.now().strftime("%H:%M:%S")

    def _log(
        self,
        message: str,
        style: str,
        prefix: str = "",
        panel: bool = False
    ) -> None:
        """
        Internal logging method.
        
        Args:
            message: The message to log
            style: Rich style to apply
            prefix: Optional prefix (emoji or symbol)
            panel: Whether to wrap in a panel
        """
        timestamp = f"[timestamp][{self._get_timestamp()}][/timestamp]"
        formatted = f"{timestamp} {prefix} [{style}]{message}[/{style}]"
        
        if panel:
            self.console.print(Panel(formatted, expand=False))
        else:
            self.console.print(formatted)

    def info(self, message: str) -> None:
        """
        Log an informational message.
        
        Args:
            message: The message to log
        """
        self._log(message, "info", "ℹ️ ")

    def scraping(self, message: str) -> None:
        """
        Log a scraping-related message (cyan).
        
        Args:
            message: The message to log
        """
        self._log(message, "scraping", "🔍")

    def email(self, message: str) -> None:
        """
        Log an email-related message (green).
        
        Args:
            message: The message to log
        """
        self._log(message, "email", "📧")

    def success(self, message: str) -> None:
        """
        Log a success message (green).
        
        Args:
            message: The message to log
        """
        self._log(message, "success", "✅")

    def warning(self, message: str) -> None:
        """
        Log a warning message (yellow).
        
        Args:
            message: The message to log
        """
        self._log(message, "warning", "⚠️ ")

    def error(self, message: str) -> None:
        """
        Log an error message (red).
        
        Args:
            message: The message to log
        """
        self._log(message, "error", "❌")

    def status(self, message: str) -> None:
        """
        Log a status change message (magenta).
        
        Args:
            message: The message to log
        """
        self._log(message, "status", "🔄")

    def startup(self) -> None:
        """Log the startup banner."""
        banner = Text()
        banner.append("\n")
        banner.append("╔══════════════════════════════════════╗\n", style="bold cyan")
        banner.append("║      ", style="bold cyan")
        banner.append("LeadSniper Worker", style="bold white")
        banner.append("              ║\n", style="bold cyan")
        banner.append("║      ", style="bold cyan")
        banner.append("v1.0.0", style="dim white")
        banner.append("                          ║\n", style="bold cyan")
        banner.append("╚══════════════════════════════════════╝\n", style="bold cyan")
        self.console.print(banner)

    def heartbeat(self, pending: int, queued: int) -> None:
        """
        Log a heartbeat status showing pending work.
        
        Args:
            pending: Number of domains pending scraping
            queued: Number of emails queued for sending
        """
        self.console.print(
            f"[timestamp][{self._get_timestamp()}][/timestamp] "
            f"💓 Heartbeat: "
            f"[scraping]{pending}[/scraping] pendientes, "
            f"[email]{queued}[/email] en cola"
        )

    def separator(self) -> None:
        """Print a visual separator line."""
        self.console.print("─" * 50, style="dim white")

    def stats(self, stats: dict) -> None:
        """
        Log statistics about lead statuses.
        
        Args:
            stats: Dictionary with status counts
        """
        self.console.print("\n[bold white]📊 Estadísticas:[/bold white]")
        for status, count in stats.items():
            color = "green" if status in ["sent", "scraped"] else "yellow" if status == "pending" else "white"
            self.console.print(f"   [{color}]{status}:[/{color}] {count}")
        self.console.print()


# Global logger instance for convenience
log = Logger()
