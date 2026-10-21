"""MCP client selecting official SDK if installed; core-stdio fallback for offline demo.

The fallback implements a small subset and is labeled as such. The official
transport is tested in GitHub Actions, which installs requirements.txt.
"""
from __future__ import annotations
import asyncio
import importlib.util
import json
import os
import subprocess
import sys
import threading
from typing import Any

class MCPError(RuntimeError):
    pass

class MCPClient:
    def __init__(self, workspace: str = 'demo'):
        from app.core import workspace_id
        self.workspace=workspace_id(workspace)
        protocol=os.environ.get('MCP_PROTOCOL','auto').lower()
        if protocol not in {'auto','official','fallback'}:
            raise ValueError('MCP_PROTOCOL must be auto, official or fallback')
        has_sdk=importlib.util.find_spec('mcp') is not None
        self.protocol='official_sdk' if protocol!='fallback' and has_sdk else 'minimal_stdio_fallback'
        if protocol=='official' and not has_sdk:
            raise MCPError('MCP official SDK is not installed')
        if self.protocol=='official_sdk':
            self._official_start()
        else:
            self._fallback_start()

    def _official_start(self):
        self._ready=threading.Event()
        self._ready_error=None
        self._thread=threading.Thread(target=self._official_thread,daemon=True)
        self._thread.start()
        if not self._ready.wait(20):
            raise MCPError('official MCP server startup timed out')
        if self._ready_error:
            raise MCPError('official MCP failed to start: '+str(self._ready_error))

    def _official_thread(self):
        try:
            asyncio.run(self._official_runner())
        except BaseException as exc:
            self._ready_error=exc
            self._ready.set()

    async def _official_runner(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        env=os.environ.copy()
        env['FDE_WORKSPACE']=self.workspace
        params=StdioServerParameters(command=sys.executable,args=['-m','app.mcp_official'],env=env)
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                self._loop=asyncio.get_running_loop()
                self._session=session
                self._stop=asyncio.Event()
                self._ready.set()
                await self._stop.wait()

    def _official_request(self,command:str,name:str='',params:dict[str,Any]|None=None):
        async def go():
            if command=='list':
                result=await self._session.list_tools()
                return [{'name':t.name,'description':t.description or ''} for t in result.tools]
            response=await self._session.call_tool(name,params or {})
            if response.isError:
                raise MCPError('MCP tool error: '+str(response.content[0].text)[:250])
            # SDK may expose structuredContent with result wrapper; text preserves
            # exact tool payload across 1.x SDK variants.
            for item in response.content:
                if getattr(item,'type',None)=='text':
                    try: return json.loads(item.text)
                    except (ValueError,TypeError): pass
            structured=getattr(response,'structuredContent',None)
            if isinstance(structured,dict):
                return structured.get('result',structured)
            raise MCPError('empty or unparseable MCP tool result')
        future=asyncio.run_coroutine_threadsafe(go(),self._loop)
        try: return future.result(timeout=20)
        except TimeoutError:
            future.cancel();raise MCPError('official MCP call timed out')

    def _fallback_start(self):
        env=os.environ.copy()
        env['FDE_WORKSPACE']=self.workspace
        self.proc=subprocess.Popen([sys.executable,'-m','app.mcp_stdio'],stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,
                                   encoding='utf-8',bufsize=1,env=env)
        self.counter=0
        self._fallback_request('initialize',{'protocolVersion':'2024-11-05','capabilities':{},
                               'clientInfo':{'name':'fde-agent','version':'0.2.0'}})
        self.proc.stdin.write(json.dumps({'jsonrpc':'2.0','method':'notifications/initialized'})+'\n')
        self.proc.stdin.flush()

    def _fallback_request(self,method:str,params:dict|None=None)->dict:
        if self.proc.poll() is not None:
            raise MCPError('fallback MCP server stopped')
        self.counter+=1
        req={'jsonrpc':'2.0','id':self.counter,'method':method}
        if params is not None: req['params']=params
        self.proc.stdin.write(json.dumps(req,ensure_ascii=False)+'\n');self.proc.stdin.flush()
        lines=[]
        task=threading.Thread(target=lambda:lines.append(self.proc.stdout.readline()),daemon=True)
        task.start();task.join(timeout=8)
        if task.is_alive():
            self.close();raise MCPError('fallback MCP response timed out')
        if not lines or not lines[0]:
            raise MCPError('fallback MCP empty response')
        value=json.loads(lines[0])
        if value.get('id')!=self.counter or 'error' in value:
            raise MCPError(str(value.get('error') or 'MCP response ID mismatch'))
        return value['result']

    def tools(self)->list[dict[str,Any]]:
        return self._official_request('list') if self.protocol=='official_sdk' else self._fallback_request('tools/list')['tools']

    def call(self,name:str,**kwargs)->Any:
        if self.protocol=='official_sdk':
            return self._official_request('call',name,kwargs)
        r=self._fallback_request('tools/call',{'name':name,'arguments':kwargs})
        if r.get('isError'):
            raise MCPError(r['content'][0].get('text','MCP tool failed'))
        return json.loads(r['content'][0]['text'])

    def close(self):
        if self.protocol=='official_sdk':
            if getattr(self,'_loop',None) and getattr(self,'_stop',None):
                self._loop.call_soon_threadsafe(self._stop.set)
                self._thread.join(timeout=8)
            return
        if self.proc.poll() is None:
            self.proc.terminate()
            try:self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait(timeout=2)
        for stream in (self.proc.stdin,self.proc.stdout):
            if stream: stream.close()

    def __enter__(self):return self
    def __exit__(self,*_):self.close()
