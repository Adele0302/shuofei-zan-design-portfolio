"""MCP stdio client used by the agent for real tool calls, not function mocks."""
from __future__ import annotations
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

class MCPError(RuntimeError): pass

class MCPClient:
    def __init__(self) -> None:
        env=os.environ.copy()
        self.proc=subprocess.Popen([sys.executable,'-m','app.mcp_stdio'],stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                                   encoding='utf-8',bufsize=1,env=env)
        self.counter=0
        self._request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},
                                    'clientInfo':{'name':'fde-procurement-agent','version':'0.1.0'}})
        self.proc.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n')
        self.proc.stdin.flush()

    def _request(self,method: str,params: dict[str,Any] | None=None) -> dict[str,Any]:
        if self.proc.poll() is not None: raise MCPError('MCP server stopped')
        self.counter+=1
        req={'jsonrpc':'2.0','id':self.counter,'method':method}
        if params is not None: req['params']=params
        self.proc.stdin.write(json.dumps(req,ensure_ascii=False)+'\n')
        self.proc.stdin.flush()
        output=[]
        def reader(): output.append(self.proc.stdout.readline())
        worker=threading.Thread(target=reader,daemon=True);worker.start();worker.join(timeout=8)
        if worker.is_alive():
            self.close();raise MCPError('MCP response timeout')
        if not output or not output[0]: raise MCPError('MCP empty response')
        msg=json.loads(output[0])
        if msg.get('id')!=self.counter or 'error' in msg:
            raise MCPError(str(msg.get('error') or 'MCP response ID mismatch'))
        return msg['result']

    def tools(self) -> list[dict[str,Any]]: return self._request('tools/list')['tools']

    def call(self, name: str, **kwargs) -> Any:
        result=self._request('tools/call',{'name':name,'arguments':kwargs})
        if result.get('isError'): raise MCPError(result['content'][0].get('text','tool failed'))
        return json.loads(result['content'][0]['text'])

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try: self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired: self.proc.kill();self.proc.wait(timeout=2)
        for obj in (self.proc.stdin,self.proc.stdout,self.proc.stderr):
            if obj: obj.close()

    def __enter__(self): return self
    def __exit__(self, *_): self.close()
