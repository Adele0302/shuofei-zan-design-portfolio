from app.agent import run_agent
from app.mcp_client import MCPClient, MCPError
from app.core import get_ticket


def test_mcp_handshake_and_tool_list():
    with MCPClient() as cli:
        assert 'search_knowledge' in {tool['name'] for tool in cli.tools()}
        assert 'create_ticket_draft' in {tool['name'] for tool in cli.tools()}


def test_mcp_search_has_source(seeded):
    with MCPClient() as cli:
        hits=cli.call('search_knowledge',query='供应商A打样周期',top_k=2)
        assert hits and hits[0]['source']=='02_供应商与打样.md'


def test_agent_grounding_and_trace(seeded):
    result=run_agent('BOM的ECO变更流程是什么？')
    assert result['mode']=='extractive_offline'
    assert result['sources'] and result['tool_trace'][0]['tool']=='search_knowledge'
    assert result['ticket'] is None


def test_agent_draft_and_human_gate(seeded):
    result=run_agent('创建工单：供应商A打样尺寸偏差如何处理？')
    assert result['ticket'] and result['ticket']['status']=='draft'
    assert result['requires_human_approval']
    assert get_ticket(result['ticket']['id'])['status']=='draft'


def test_agent_no_draft_without_evidence(seeded):
    result=run_agent('创建工单：火星殖民舰队的发射许可码是多少？')
    assert result['ticket'] is None and not result['requires_human_approval']


def test_unknown_mcp_tool(seeded):
    with MCPClient() as cli:
        try: cli.call('nonexistent_tool')
        except MCPError as exc: assert 'unknown' in str(exc)
        else: raise AssertionError('unknown tool should fail')
