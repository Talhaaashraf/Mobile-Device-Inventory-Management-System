from pathlib import Path
import re
p = Path('frontend/src/api/client.js')
text = p.read_text()
text = re.sub(r'config\.headers\.Authorization = `[^\n]*;', 'config.headers.Authorization = `Bearer ${access}`;', text)
text = re.sub(r'original\.headers\.Authorization = `[^\n]*;', 'original.headers.Authorization = `Bearer ${token}`;', text)
p.write_text(text)
print('patched')
