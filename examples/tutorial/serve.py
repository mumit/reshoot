"""Serve a local review copy with byte ranges so browsers can seek within MP4s."""
from functools import partial
import http.server
from pathlib import Path
import re


class MediaHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Accept-Ranges','bytes')
        super().end_headers()

    def send_head(self):
        self.remaining=None
        path=Path(self.translate_path(self.path))
        if not path.resolve().is_relative_to(Path(self.directory).resolve()):
            self.send_error(403);return None
        requested=self.headers.get('Range')
        if not requested or not path.is_file():return super().send_head()
        size=path.stat().st_size
        if self.headers.get('If-Range') and self.headers['If-Range']!=self.date_time_string(path.stat().st_mtime):
            return super().send_head()
        match=re.fullmatch(r'bytes=(\d*)-(\d*)',requested)
        if match and any(match.groups()) and size:
            left,right=match.groups()
            if left:
                start=int(left);end=min(int(right) if right else size-1,size-1)
            else:
                start=max(0,size-int(right));end=size-1
            if 0<=start<=end<size:
                file=path.open('rb');file.seek(start)
                self.remaining=end-start+1
                self.send_response(206)
                self.send_header('Content-Type',self.guess_type(str(path)))
                self.send_header('Content-Length',str(self.remaining))
                self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
                self.send_header('Last-Modified',self.date_time_string(path.stat().st_mtime))
                self.end_headers();return file
        self.send_response(416)
        self.send_header('Content-Range',f'bytes */{size}')
        self.send_header('Content-Length','0');self.end_headers()
        return None

    def copyfile(self,source,outputfile):
        try:
            if self.remaining is None:return super().copyfile(source,outputfile)
            while self.remaining:
                data=source.read(min(self.remaining,65536))
                if not data:break
                outputfile.write(data);self.remaining-=len(data)
        except (BrokenPipeError,ConnectionResetError):
            pass # Browsers cancel a range when the viewer seeks elsewhere.


def serve(folder, port=8800):
    server=http.server.ThreadingHTTPServer(('127.0.0.1',port),partial(MediaHandler,directory=str(folder)))
    print(f'Local review: http://127.0.0.1:{server.server_port}/review/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
