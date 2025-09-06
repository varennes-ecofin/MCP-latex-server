"""
MCP Server for LaTeX integration with Claude Desktop.

Version: 1.2.0 - Fixed initialization
License: MIT
"""

Author: MCP LaTeX Server
Version: 1.2.0 - Fixed initialization
License: MIT
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
import shutil
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

# MCP SDK imports - Install with: pip install mcp
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from mcp.server.stdio import stdio_server
except ImportError as e:
    print(f"Error importing MCP: {e}", file=sys.stderr)
    print("Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Optional imports
try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False
    print("Warning: aiofiles not available. Using synchronous file operations.", file=sys.stderr)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LaTeXServer:
    """
    Main MCP server class for LaTeX operations.
    Handles file management, compilation, validation and template generation.
    """
    
    def __init__(self, workspace_dir: str = None):
        """
        Initialize the LaTeX MCP server.
        
        Args:
            workspace_dir: Default workspace directory for LaTeX projects
        """
        self.server = Server("latex-server")
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        
        # Ensure workspace directory exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Supported LaTeX engines
        self.supported_engines = ['pdflatex', 'lualatex', 'xelatex', 'bibtex', 'biber']
        
        # File extensions categorization
        self.supported_extensions = {
            'source': ['.tex', '.bib', '.cls', '.sty', '.bst'],
            'auxiliary': ['.aux', '.log', '.bbl', '.blg', '.toc', '.lof', '.lot', 
                        '.idx', '.ind', '.out', '.nav', '.snm', '.vrb', '.fls', 
                        '.fdb_latexmk', '.synctex.gz', '.bcf', '.run.xml'],
            'output': ['.pdf', '.dvi', '.ps']
        }
        
        # Supported document classes
        self.document_classes = ['article', 'report', 'book', 'letter', 'beamer', 
                                'memoir', 'scrartcl', 'scrreprt', 'scrbook']
        
        # Detect TeX distribution
        self.tex_distribution = self._detect_tex_distribution()
        logger.info(f"Detected TeX distribution: {self.tex_distribution or 'None'}")
        
        # Register all tools
        self._register_tools()
    
    def _detect_tex_distribution(self) -> Optional[str]:
        """
        Detect installed TeX distribution.
        
        Returns:
            Name of detected distribution or None
        """
        try:
            # Try to run tex command
            result = subprocess.run(['tex', '--version'], 
                                capture_output=True, text=True, timeout=5)
            if 'TeX Live' in result.stdout:
                return 'texlive'
            elif 'MiKTeX' in result.stdout:
                return 'miktex'
        except Exception:
            pass
        
        # Check common installation paths
        if sys.platform == 'win32':
            if Path('C:/texlive').exists():
                return 'texlive'
            elif Path('C:/Program Files/MiKTeX').exists() or Path('C:/Program Files (x86)/MiKTeX').exists():
                return 'miktex'
        else:
            if Path('/usr/local/texlive').exists() or Path('/opt/texlive').exists():
                return 'texlive'
        
        logger.warning("No TeX distribution detected. Compilation features may not work.")
        return None
    
    def _get_full_path(self, filename: str, path: Optional[str] = None) -> Path:
        """
        Get full path for a file.
        
        Args:
            filename: Name of the file
            path: Optional path relative to workspace
            
        Returns:
            Full path to the file
        """
        if path:
            base_path = Path(path)
            if base_path.is_absolute():
                return base_path / filename
            return self.workspace_dir / path / filename
        return self.workspace_dir / filename

    def _get_latex_template(self, document_class: str, options: Optional[Dict] = None) -> str:
        """
        Generate LaTeX template for given document class.
        
        Args:
            document_class: LaTeX document class
            options: Additional options for template
            
        Returns:
            LaTeX template as string
        """
        options = options or {}
        
        # Basic templates by document class
        templates = {
            'article': '''\\documentclass[11pt,a4paper]{article}

\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{lmodern}
\\usepackage[english]{babel}
\\usepackage{amsmath,amssymb,amsthm}
\\usepackage{graphicx}
\\usepackage{hyperref}

\\title{Your Title Here}
\\author{Your Name}
\\date{\\today}

\\begin{document}

\\maketitle

\\begin{abstract}
Your abstract here.
\\end{abstract}

\\section{Introduction}

Your content here.

\\section{Conclusion}

Your conclusion here.

\\end{document}''',
            
            'report': '''\\documentclass[11pt,a4paper]{report}

\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{lmodern}
\\usepackage[english]{babel}
\\usepackage{amsmath,amssymb,amsthm}
\\usepackage{graphicx}
\\usepackage{hyperref}

\\title{Your Report Title}
\\author{Your Name}
\\date{\\today}

\\begin{document}

\\maketitle
\\tableofcontents

\\chapter{Introduction}

Your introduction here.

\\chapter{Main Content}

Your main content here.

\\chapter{Conclusion}

Your conclusion here.

\\end{document}''',
            
            'beamer': '''\\documentclass{beamer}

\\usetheme{Madrid}
\\usecolortheme{default}

\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{lmodern}
\\usepackage[english]{babel}
\\usepackage{amsmath,amssymb}

\\title{Your Presentation Title}
\\author{Your Name}
\\institute{Your Institution}
\\date{\\today}

\\begin{document}

\\frame{\\titlepage}

\\begin{frame}
\\frametitle{Table of Contents}
\\tableofcontents
\\end{frame}

\\section{Introduction}
\\begin{frame}
\\frametitle{Introduction}
\\begin{itemize}
\\item Your first point
\\item Your second point
\\item Your third point
\\end{itemize}
\\end{frame}

\\section{Conclusion}
\\begin{frame}
\\frametitle{Conclusion}
Your conclusion here.
\\end{frame}

\\end{document}'''
        }
        
        return templates.get(document_class, templates['article'])

    async def _read_file_async(self, file_path: Path) -> str:
        """
        Read file asynchronously if aiofiles is available, synchronously otherwise.
        
        Args:
            file_path: Path to file
            
        Returns:
            File content as string
        """
        if AIOFILES_AVAILABLE:
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    return await f.read()
            except Exception:
                # Fallback to sync
                pass
        
        # Synchronous fallback
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    async def _write_file_async(self, file_path: Path, content: str) -> None:
        """
        Write file asynchronously if aiofiles is available, synchronously otherwise.
        
        Args:
            file_path: Path to file
            content: Content to write
        """
        if AIOFILES_AVAILABLE:
            try:
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
                return
            except Exception:
                # Fallback to sync
                pass
        
        # Synchronous fallback
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _register_tools(self):
        """Register all available tools with the MCP server."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available LaTeX tools."""
            return [
                Tool(
                    name="create_latex_file",
                    description="Create a new LaTeX file with optional template",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Name of the file to create"},
                            "content": {"type": "string", "description": "Content of the file"},
                            "template": {"type": "string", "description": "Template type (article, report, book, beamer, etc.)"},
                            "path": {"type": "string", "description": "Path relative to workspace"}
                        },
                        "required": ["filename"]
                    }
                ),
                Tool(
                    name="read_latex_file",
                    description="Read content of a LaTeX file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Name of the file to read"},
                            "path": {"type": "string", "description": "Path relative to workspace"}
                        },
                        "required": ["filename"]
                    }
                ),
                Tool(
                    name="edit_latex_file",
                    description="Edit an existing LaTeX file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Name of the file to edit"},
                            "content": {"type": "string", "description": "New content of the file"},
                            "path": {"type": "string", "description": "Path relative to workspace"}
                        },
                        "required": ["filename", "content"]
                    }
                ),
                Tool(
                    name="compile_latex",
                    description="Compile a LaTeX document",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Main .tex file to compile"},
                            "engine": {"type": "string", "description": "LaTeX engine (pdflatex, lualatex, xelatex)"},
                            "bibtex": {"type": "boolean", "description": "Run BibTeX/Biber"},
                            "path": {"type": "string", "description": "Path relative to workspace"}
                        },
                        "required": ["filename"]
                    }
                ),
                Tool(
                    name="validate_latex_syntax",
                    description="Validate LaTeX syntax and check for common errors",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "File to validate"},
                            "path": {"type": "string", "description": "Path relative to workspace"}
                        },
                        "required": ["filename"]
                    }
                ),
                Tool(
                    name="list_latex_files",
                    description="List all LaTeX-related files in a directory",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to list files from"},
                            "include_auxiliary": {"type": "boolean", "description": "Include auxiliary files"}
                        }
                    }
                ),
                Tool(
                    name="clean_latex_auxiliary",
                    description="Clean auxiliary files generated during compilation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Path to clean"},
                            "keep_pdf": {"type": "boolean", "description": "Keep PDF files"}
                        }
                    }
                ),
                Tool(
                    name="get_latex_template",
                    description="Get a LaTeX template for a specific document type",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "document_class": {"type": "string", "description": "Document class"},
                            "options": {"type": "object", "description": "Template options"}
                        },
                        "required": ["document_class"]
                    }
                ),                
                Tool(
                    name="change_workspace",
                    description="Change the current workspace directory for LaTeX operations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "new_workspace": {
                                "type": "string", 
                                "description": "Path to the new workspace directory"
                            }
                        },
                        "required": ["new_workspace"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Execute a tool and return the result."""
            try:
                logger.info(f"Executing tool: {name} with arguments: {arguments}")
                result = {}
                
                if name == "create_latex_file":
                    result = await self.create_latex_file(**arguments)
                elif name == "read_latex_file":
                    result = await self.read_latex_file(**arguments)
                elif name == "edit_latex_file":
                    result = await self.edit_latex_file(**arguments)
                elif name == "compile_latex":
                    result = await self.compile_latex(**arguments)
                elif name == "validate_latex_syntax":
                    result = await self.validate_latex_syntax(**arguments)
                elif name == "list_latex_files":
                    result = await self.list_latex_files(**arguments)
                elif name == "clean_latex_auxiliary":
                    result = await self.clean_latex_auxiliary(**arguments)
                elif name == "get_latex_template":
                    result = await self.get_latex_template(**arguments)
                elif name == "change_workspace":
                    result = await self.change_workspace(**arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

    # Tool implementation methods (keeping the existing implementations)
    async def create_latex_file(self, filename: str, content: str = None, 
                                template: str = None, path: str = None) -> Dict[str, Any]:
        """Create a new LaTeX file with optional template."""
        try:
            file_path = self._get_full_path(filename, path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if content is None:
                if template:
                    content = self._get_latex_template(template)
                else:
                    content = self._get_latex_template('article')
            
            await self._write_file_async(file_path, content)
            
            return {
                "success": True,
                "message": f"Created LaTeX file: {file_path}",
                "path": str(file_path),
                "template_used": template or "article"
            }
            
        except Exception as e:
            return {"error": f"Failed to create file: {str(e)}"}

    async def read_latex_file(self, filename: str, path: str = None) -> Dict[str, Any]:
        """Read content of a LaTeX file."""
        try:
            file_path = self._get_full_path(filename, path)
            
            if not file_path.exists():
                return {"error": f"File does not exist: {file_path}"}
            
            content = await self._read_file_async(file_path)
            
            return {
                "success": True,
                "path": str(file_path),
                "content": content,
                "size": len(content),
                "lines": len(content.split('\n'))
            }
            
        except Exception as e:
            return {"error": f"Failed to read file: {str(e)}"}

    async def edit_latex_file(self, filename: str, content: str, path: str = None) -> Dict[str, Any]:
        """Edit an existing LaTeX file."""
        try:
            file_path = self._get_full_path(filename, path)
            
            if file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + '.bak')
                shutil.copy2(file_path, backup_path)
            
            await self._write_file_async(file_path, content)
            
            return {
                "success": True,
                "message": f"Updated LaTeX file: {file_path}",
                "path": str(file_path),
                "backup_created": file_path.exists()
            }
            
        except Exception as e:
            return {"error": f"Failed to edit file: {str(e)}"}

    async def compile_latex(self, filename: str, engine: str = "pdflatex", 
                            bibtex: bool = False, path: str = None) -> Dict[str, Any]:
        """Compile a LaTeX document."""
        try:
            file_path = self._get_full_path(filename, path)
            
            if not file_path.exists():
                return {"error": f"File does not exist: {file_path}"}
            
            if not file_path.suffix == '.tex':
                return {"error": "File must have .tex extension"}
            
            if engine not in self.supported_engines:
                return {"error": f"Unsupported engine: {engine}"}
            
            original_cwd = os.getcwd()
            os.chdir(file_path.parent)
            
            results = {}
            
            try:
                cmd = [engine, '-interaction=nonstopmode', file_path.name]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                results['latex_output'] = result.stdout
                results['latex_errors'] = result.stderr
                results['latex_returncode'] = result.returncode
                
                if bibtex:
                    bib_files = list(file_path.parent.glob('*.bib'))
                    if bib_files:
                        bib_cmd = ['bibtex', file_path.stem]
                        bib_result = subprocess.run(bib_cmd, capture_output=True, text=True, timeout=30)
                        results['bibtex_output'] = bib_result.stdout
                        results['bibtex_errors'] = bib_result.stderr
                        
                        result2 = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                        results['latex_output_2'] = result2.stdout
                
                pdf_path = file_path.with_suffix('.pdf')
                results['pdf_generated'] = pdf_path.exists()
                if results['pdf_generated']:
                    results['pdf_path'] = str(pdf_path)
                
                results['success'] = result.returncode == 0
                
            finally:
                os.chdir(original_cwd)
            
            return results
            
        except subprocess.TimeoutExpired:
            return {"error": "Compilation timed out"}
        except Exception as e:
            return {"error": f"Compilation failed: {str(e)}"}

    async def validate_latex_syntax(self, filename: str, path: str = None) -> Dict[str, Any]:
        """Validate LaTeX syntax and check for common errors."""
        try:
            file_path = self._get_full_path(filename, path)
            
            if not file_path.exists():
                return {"error": f"File does not exist: {file_path}"}
            
            content = await self._read_file_async(file_path)
            
            warnings = []
            errors = []
            
            lines = content.split('\n')
            
            # Check for balanced braces
            brace_count = 0
            for i, line in enumerate(lines, 1):
                for char in line:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count < 0:
                            errors.append(f"Line {i}: Unmatched closing brace")
                            brace_count = 0
            
            if brace_count > 0:
                errors.append(f"Unmatched opening braces: {brace_count}")
            
            # Check for document structure
            has_documentclass = bool(re.search(r'\\documentclass', content))
            has_begin_document = bool(re.search(r'\\begin\{document\}', content))
            has_end_document = bool(re.search(r'\\end\{document\}', content))
            
            if not has_documentclass:
                errors.append("Missing \\documentclass command")
            if not has_begin_document:
                errors.append("Missing \\begin{document}")
            if not has_end_document:
                errors.append("Missing \\end{document}")
            
            # Check for common issues
            if '$' in content and content.count('$') % 2 != 0:
                warnings.append("Unmatched math mode delimiters ($)")
            
            # Check for undefined references
            refs = re.findall(r'\\ref\{([^}]+)\}', content)
            labels = re.findall(r'\\label\{([^}]+)\}', content)
            undefined_refs = [ref for ref in refs if ref not in labels]
            
            if undefined_refs:
                warnings.append(f"Potentially undefined references: {', '.join(undefined_refs)}")
            
            return {
                "success": True,
                "path": str(file_path),
                "errors": errors,
                "warnings": warnings,
                "is_valid": len(errors) == 0,
                "structure_complete": has_documentclass and has_begin_document and has_end_document
            }
            
        except Exception as e:
            return {"error": f"Validation failed: {str(e)}"}

    async def list_latex_files(self, path: str = None, include_auxiliary: bool = False) -> Dict[str, Any]:
        """List all LaTeX-related files in a directory."""
        try:
            dir_path = Path(path) if path else self.workspace_dir
            if not dir_path.is_absolute():
                dir_path = self.workspace_dir / path
            
            if not dir_path.exists():
                return {"error": f"Directory does not exist: {dir_path}"}
            
            files = {
                'source_files': [],
                'output_files': [],
                'auxiliary_files': []
            }
            
            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    suffix = file_path.suffix.lower()
                    
                    if suffix in self.supported_extensions['source']:
                        files['source_files'].append({
                            'name': file_path.name,
                            'path': str(file_path),
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
                    elif suffix in self.supported_extensions['output']:
                        files['output_files'].append({
                            'name': file_path.name,
                            'path': str(file_path),
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
                    elif suffix in self.supported_extensions['auxiliary'] and include_auxiliary:
                        files['auxiliary_files'].append({
                            'name': file_path.name,
                            'path': str(file_path),
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        })
            
            return {
                "success": True,
                "directory": str(dir_path),
                "files": files,
                "total_source": len(files['source_files']),
                "total_output": len(files['output_files']),
                "total_auxiliary": len(files['auxiliary_files'])
            }
            
        except Exception as e:
            return {"error": f"Failed to list files: {str(e)}"}

    async def clean_latex_auxiliary(self, path: str = None, keep_pdf: bool = True) -> Dict[str, Any]:
        """Clean auxiliary files generated during compilation."""
        try:
            if path is None:
                dir_path = self.workspace_dir
            else:
                dir_path = Path(path)
                if not dir_path.is_absolute():
                    dir_path = self.workspace_dir / path
            
            if not dir_path.exists():
                return {"error": f"Directory does not exist: {dir_path}"}
            
            removed_files = []
            total_size = 0
            
            extensions_to_remove = self.supported_extensions['auxiliary'].copy()
            if not keep_pdf:
                extensions_to_remove.extend(self.supported_extensions['output'])
            elif '.pdf' in extensions_to_remove:
                extensions_to_remove.remove('.pdf')
            
            for file_path in dir_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in extensions_to_remove:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    removed_files.append(file_path.name)
                    total_size += size
            
            return {
                "success": True,
                "directory": str(dir_path),
                "removed_files": removed_files,
                "total_files": len(removed_files),
                "total_size": total_size,
                "pdf_kept": keep_pdf
            }
            
        except Exception as e:
            return {"error": f"Failed to clean files: {str(e)}"}

    async def get_latex_template(self, document_class: str, options: Dict = None) -> Dict[str, Any]:
        """Get a LaTeX template for a specific document type."""
        try:
            if document_class not in self.document_classes:
                return {
                    "error": f"Unsupported document class: {document_class}",
                    "supported_classes": self.document_classes
                }
            
            template = self._get_latex_template(document_class, options)
            
            return {
                "success": True,
                "document_class": document_class,
                "template": template,
                "options": options or {}
            }
            
        except Exception as e:
            return {"error": f"Failed to generate template: {str(e)}"}
    
    async def run(self):
        """Run the MCP server with correct initialization."""
        logger.info(f"Starting LaTeX MCP Server with workspace: {self.workspace_dir}")
        try:
            async with stdio_server() as (read_stream, write_stream):
                # FIXED: Use create_initialization_options() instead of empty dict
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            print(f"Server error: {str(e)}", file=sys.stderr)
            raise

    async def change_workspace(self, new_workspace: str) -> Dict[str, Any]:
        """
        Change the current workspace directory.
        
        Args:
            new_workspace: Path to the new workspace directory
            
        Returns:
            Dictionary with operation result
        """
        try:
            new_path = Path(new_workspace).resolve()
            
            # Create directory if it doesn't exist
            new_path.mkdir(parents=True, exist_ok=True)
            
            # Store old workspace for reference
            old_workspace = str(self.workspace_dir)
            
            # Update workspace
            self.workspace_dir = new_path
            
            return {
                "success": True,
                "message": "Workspace changed successfully",
                "old_workspace": old_workspace,
                "new_workspace": str(new_path)
            }
            
        except Exception as e:
            return {"error": f"Failed to change workspace: {str(e)}"}

def main():
    """Main entry point for the MCP LaTeX Server."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='MCP Server for LaTeX integration with Claude Desktop',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python mcp_latex_server.py --workspace C:/LaTeX/Projects
    python mcp_latex_server.py --workspace ~/Documents/LaTeX

For more information, visit the documentation.
        """
    )
    
    parser.add_argument(
        '--workspace', 
        type=str, 
        default=os.getcwd(),
        help='Default workspace directory for LaTeX projects (default: current directory)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set the logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='MCP LaTeX Server 1.2.0 - Fixed'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and run server
    try:
        server = LaTeXServer(workspace_dir=args.workspace)
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("Server stopped by user", file=sys.stderr)
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        print(f"Server error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":

    main()
