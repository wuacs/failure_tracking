import base64
import hashlib
import io
import re
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')  # Use non-GUI backend
from aqt import QApplication, QPalette

_global_cache = {}

def _palette_text_color_hex():
    if not QApplication:
        return "#000000"
    app = QApplication.instance()
    if not app:
        return "#000000"
    pal = app.palette()
    c = pal.color(QPalette.ColorRole.Text)
    return f"#{c.red():02x}{c.green():02x}{c.blue():02x}"

def render_latex_to_svg(latex_code: str, display_mode: bool = False) -> str:
    """Convert LaTeX to SVG data URL for use in img tags"""
    try:
        # Create cache key
        cache_key = hashlib.md5(f"{latex_code}_{display_mode}".encode()).hexdigest()
        if cache_key in _global_cache:
            return _global_cache[cache_key]

        print(f"DEBUG: Attempting to render LaTeX: '{latex_code}'")
                
        # Configure matplotlib for LaTeX
        plt.rcParams['text.usetex'] = False
        plt.rcParams['mathtext.fontset'] = 'cm'
        
        # Create a very minimal figure
        fig, ax = plt.subplots(figsize=(1, 1))
        
        fontsize = 28 if display_mode else 22
                
        # Render the text
        text_obj = ax.text(0.5, 0.5, f'${latex_code}$', 
                        horizontalalignment='center', 
                        verticalalignment='center',
                        fontsize=fontsize,
                        transform=ax.transAxes,
                        color=_palette_text_color_hex()) 

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
                dpi=300,
                pad_inches=0.02)
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
        _global_cache[cache_key] = data_url
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

def process_latex_in_text(text: str) -> str:
    """Replace LaTeX expressions with img tags containing SVG data URLs"""
    # Display math: $$...$$
    def replace_display_math(match):
        latex = match.group(1).strip()
        if not latex:
            return match.group(0)
        svg_data_url = render_latex_to_svg(latex, display_mode=True)
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
        svg_data_url = render_latex_to_svg(latex, display_mode=False)
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