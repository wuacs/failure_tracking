from typing import Dict, cast
from aqt import QComboBox, QListWidgetItem, QTextEdit, QWidget, mw, QListWidget, QDialog, QPushButton
from ..db import insert_failure, list_tags
from ..ui import Ui_CreateFailure
from ..model import FailureTag
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextDocument, QTextImageFormat, QTextCursor
import re
import base64
import io
import hashlib
import sys
import os

class CreateFailure(QDialog):
    required = [
        "failure_description_text","save_failure_button","cancel_failure_button",
        "tags_combobox","tags_list","add_tag_button",
    ]

    def __init__(self, card_id:int, parent=None):
        super().__init__(parent or mw)
        self.ui = Ui_CreateFailure(); self.ui.setupUi(self)
        self.card_id = card_id
        self.widgets: Dict[str, QWidget] = {n: getattr(self.ui, n) for n in self.required}
        
        # Add libs directory to Python path
        self._setup_matplotlib_path()
        
        # Cache for rendered LaTeX images
        self._latex_cache = {}
        
        self._setup_markdown_preview()
        self._hide_unused_widgets()
        self._setup_tags(); self._setup_save_button(); self._setup_cancel_button()

    def _setup_matplotlib_path(self):
        """Add the bundled matplotlib to Python path"""
        addon_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from dialogs/ to addon root
        libs_dir = os.path.join(addon_dir, 'libs')
        if os.path.exists(libs_dir) and libs_dir not in sys.path:
            sys.path.insert(0, libs_dir)
            print(f"DEBUG: Added {libs_dir} to Python path")

    def _setup_markdown_preview(self):
        """Set up markdown preview with LaTeX support"""
        if hasattr(self.ui, 'failure_description_preview'):
            # The preview is already a QTextEdit in the UI file
            self.preview_widget = cast(QTextEdit, self.ui.failure_description_preview)
            self.preview_widget.setReadOnly(True)
            self.preview_widget.setPlainText("Preview will appear here...")
            
            # Add live preview update
            self._debounce = QTimer(self)
            self._debounce.setSingleShot(True)
            self._debounce.timeout.connect(self._update_preview)
            
            text_edit = cast(QTextEdit, self.widgets["failure_description_text"])
            text_edit.textChanged.connect(lambda: self._debounce.start(500))

    def _render_latex_to_svg(self, latex_code: str, display_mode: bool = False) -> str:
        """Convert LaTeX to SVG data URL for use in img tags"""
        try:
            # Create cache key
            cache_key = hashlib.md5(f"{latex_code}_{display_mode}".encode()).hexdigest()
            if cache_key in self._latex_cache:
                return self._latex_cache[cache_key]
            
            print(f"DEBUG: Attempting to render LaTeX: '{latex_code}'")
            
            # Import from bundled matplotlib
            import matplotlib
            import matplotlib.pyplot as plt
            matplotlib.use('Agg')  # Use non-GUI backend
            
            print(f"DEBUG: matplotlib imported successfully from: {matplotlib.__file__}")
            
            # Configure matplotlib for LaTeX
            plt.rcParams['text.usetex'] = False
            plt.rcParams['mathtext.fontset'] = 'cm'
            
            # Create a very minimal figure
            fig, ax = plt.subplots(figsize=(1, 1))
            
            fontsize = 28 if display_mode else 22
            
            print(f"DEBUG: Figure created, adding text: ${latex_code}$")
            
            # Render the text
            text_obj = ax.text(0.5, 0.5, f'${latex_code}$', 
                            horizontalalignment='center', 
                            verticalalignment='center',
                            fontsize=fontsize,
                            transform=ax.transAxes,
                            color='white') 

            ax.axis('off')
            
            # Set transparent background
            fig.patch.set_facecolor('none')
            fig.patch.set_alpha(0.0)
            
            print("DEBUG: Text added to figure, saving to SVG...")
            
            # Save as SVG string
            buffer = io.StringIO()
            plt.savefig(buffer, format='svg', 
                    bbox_inches='tight',
                    transparent=True,
                    dpi=300,  # High DPI for better quality
                    pad_inches=0.02)  # Small padding to prevent cutting
            plt.close(fig)
            
            # Get the SVG content
            svg_content = buffer.getvalue()
            buffer.close()
            
            # Clean up the SVG to remove unnecessary parts
            svg_content = re.sub(r'<\?xml[^>]*\?>\s*', '', svg_content)
            svg_content = re.sub(r'<!DOCTYPE[^>]*>\s*', '', svg_content)
            
            # Create SVG data URL for img tag
            svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode()
            data_url = f"data:image/svg+xml;base64,{svg_base64}"
            
            print(f"DEBUG: Successfully generated SVG data URL, length: {len(data_url)}")
            
            # Cache the result
            self._latex_cache[cache_key] = data_url
            return data_url
            
        except ImportError as e:
            print(f"DEBUG: matplotlib not available: {e}")
            # Fallback to styled text
            if display_mode:
                return f'<div style="text-align: center; font-size: 18px; font-family: serif; margin: 10px 0; background: #f9f9f9; padding: 10px; border: 1px solid #ddd;"><i>{latex_code}</i></div>'
            else:
                return f'<span style="font-family: serif; font-style: italic; background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">{latex_code}</span>'
        except Exception as e:
            print(f"DEBUG: LaTeX rendering error - Type: {type(e).__name__}, Message: {e}")
            import traceback
            traceback.print_exc()
            return f"[LaTeX Error: {latex_code}]"

    def _process_latex_in_text(self, text: str) -> str:
        """Replace LaTeX expressions with img tags containing SVG data URLs"""
        # Display math: $$...$$
        def replace_display_math(match):
            latex = match.group(1).strip()
            if not latex:
                return match.group(0)
            svg_data_url = self._render_latex_to_svg(latex, display_mode=True)
            if svg_data_url.startswith('data:'):
                # Centered img tag with SVG
                return f'<div style="text-align: center; margin: 10px 0;"><img src="{svg_data_url}" alt="LaTeX: {latex}" style="display: inline-block; vertical-align: middle;"></div>'
            else:
                return svg_data_url  # Fallback text
        
        # Inline math: $...$
        def replace_inline_math(match):
            latex = match.group(1).strip()
            if not latex:
                return match.group(0)
            svg_data_url = self._render_latex_to_svg(latex, display_mode=False)
            if svg_data_url.startswith('data:'):
                # Inline img tag with SVG
                return f'<img src="{svg_data_url}" alt="LaTeX: {latex}" style="vertical-align: middle; display: inline; margin: 0 1px;">'
            else:
                return svg_data_url  # Fallback text
        
        # Process display math first (to avoid conflicts)
        text = re.sub(r'\$\$(.*?)\$\$', replace_display_math, text, flags=re.DOTALL)
        
        # Then process inline math
        text = re.sub(r'\$([^$]+?)\$', replace_inline_math, text)
        
        return text
    def _update_preview(self):
        """Convert markdown with LaTeX to rich text"""
        if not hasattr(self, 'preview_widget'):
            return
            
        text = cast(QTextEdit, self.widgets["failure_description_text"]).toPlainText()
        if not text.strip():
            self.preview_widget.setPlainText("Preview will appear here...")
            return
        
        # First process LaTeX
        text = self._process_latex_in_text(text)
        
        # Then apply markdown formatting
        html = self._simple_markdown_to_html(text)
        self.preview_widget.setHtml(html)

    def _simple_markdown_to_html(self, text: str) -> str:
        """Convert basic markdown syntax to simple HTML for QTextEdit"""
        # Don't escape HTML if it contains img tags (from LaTeX processing)
        if '<img' not in text and '<svg' not in text:
            text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Bold: **text** or __text__
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
        
        # Italic: *text* or _text_
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
        
        # Code: `text`
        text = re.sub(r'`(.*?)`', r'<code style="background-color: #f0f0f0; padding: 2px;">\1</code>', text)
        
        # Headers: # ## ###
        text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
        
        # Line breaks (but preserve existing <br> from LaTeX processing)
        if '<br>' not in text:
            text = text.replace('\n', '<br>')

        return f'<div>{text}</div>'

    def _hide_unused_widgets(self):
        """Hide unused widgets"""
        # Hide some buttons but keep LaTeX button for inserting syntax
        if hasattr(self.ui, 'show_description_preview'):
            self.ui.show_description_preview.hide()

    # buttons / tags
    def _setup_save_button(self):
        cast(QPushButton, self.widgets["save_failure_button"]).clicked.connect(self._on_save)
    def _setup_cancel_button(self):
        cast(QPushButton, self.widgets["cancel_failure_button"]).clicked.connect(self.reject)
    def _setup_tags(self):
        combo = cast(QComboBox, self.widgets["tags_combobox"])
        btn = cast(QPushButton, self.widgets["add_tag_button"])
        combo.clear()
        for tag in list_tags():
            combo.addItem(tag.name, tag)
        btn.clicked.connect(self._on_tag_add)

    # actions
    def _on_save(self):
        reason = cast(QTextEdit, self.widgets["failure_description_text"]).toPlainText()
        if not reason.strip():
            from aqt.utils import tooltip; tooltip("Enter a non-empty reason or Cancel.", period=1500); return
        list_widget = cast(QListWidget, self.widgets["tags_list"])
        tag_ids = [list_widget.item(i).data(Qt.ItemDataRole.UserRole).tag_id for i in range(list_widget.count())]
        insert_failure(card_id=self.card_id, tags_ids=tag_ids, reason=reason)
        self.accept()

    def _on_tag_add(self):
        combo = cast(QComboBox, self.widgets["tags_combobox"])
        list_widget = cast(QListWidget, self.widgets["tags_list"])
        sel: FailureTag = combo.currentData()
        if not sel: return
        existing = {list_widget.item(i).data(Qt.ItemDataRole.UserRole).tag_id for i in range(list_widget.count())}
        if sel.tag_id not in existing:
            item = QListWidgetItem(combo.currentText())
            item.setData(Qt.ItemDataRole.UserRole, sel)
            list_widget.addItem(item)

    @classmethod
    def prompt(cls, card_id:int, parent=None)->bool:
        d = cls(card_id, parent); return d.exec() == 1