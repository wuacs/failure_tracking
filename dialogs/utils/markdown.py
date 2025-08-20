import re

def simple_markdown_to_html(text: str) -> str:
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
