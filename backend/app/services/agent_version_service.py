import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_version import AgentVersion
from app.schemas.agent_version import AgentTestResult
from app.services.agent_client import AgentClient

_IP_PATTERN = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


def _sanitize_error(msg: str) -> str:
    return _IP_PATTERN.sub("[内部地址]", msg)


async def test_connection(db: AsyncSession, version: AgentVersion) -> AgentTestResult:
    try:
        client = AgentClient(version)
        reply, _ = await client.send_message("你好")
        version.connection_status = "success"
        await db.commit()
        return AgentTestResult(status="success", reply=reply)
    except Exception as e:
        version.connection_status = "failed"
        await db.commit()
        return AgentTestResult(status="failed", error=_sanitize_error(str(e)))
