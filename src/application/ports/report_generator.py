"""Report generator port."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional


class ReportGenerator(ABC):
    """Port for generating reports in various formats.
    
    This interface will be implemented by infrastructure adapters
    for different report formats (Excel, HTML, PDF, etc.).
    """
    
    @abstractmethod
    async def generate(
        self,
        data: Dict[str, Any],
        format: str,
        output_path: Optional[Path] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Generate a report.
        
        Args:
            data: Report data to render
            format: Output format (excel, html, pdf, json)
            output_path: Optional path for the output file
            options: Additional options for report generation
            
        Returns:
            Path to the generated report
        """
        pass
    
    @abstractmethod
    def supports_format(self, format: str) -> bool:
        """Check if a format is supported.
        
        Args:
            format: The format to check
            
        Returns:
            True if format is supported
        """
        pass
    
    @abstractmethod
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate report data before generation.
        
        Args:
            data: Data to validate
            
        Returns:
            True if data is valid
        """
        pass