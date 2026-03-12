from collections.abc import AsyncGenerator

from app.llm.base import LLMAdapter
from app.models.test_case import TestCase
from app.services.agent_client import AgentClient

END_MARKER = "[END]"


class SparringRunner:
    def __init__(
        self,
        agent_client: AgentClient,
        llm: LLMAdapter,
        test_case: TestCase,
        system_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        self.agent_client = agent_client
        self.llm = llm
        self.test_case = test_case
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.conversation: list[dict] = []
        self.persona_prompt: str = self._build_persona_prompt()

    def _build_persona_prompt(self) -> str:
        first_message = self.test_case.first_message or "喂？"
        prompt = self.system_prompt + "\n\n"
        prompt += f"--- 当前用例的角色信息 ---\n"
        prompt += self.test_case.sparring_prompt + "\n\n"
        prompt += f"首轮发言：{first_message}\n"
        prompt += f"\n当对话可以自然结束时，请在回复末尾加上 {END_MARKER} 标记。"
        return prompt

    async def run_iter(self) -> AsyncGenerator[tuple[list[dict], str | None, int], None]:
        """Run the sparring conversation loop, yielding after each round.

        Yields:
            tuple: (conversation, termination_reason, actual_rounds)
            - termination_reason is None while the conversation is ongoing
            - termination_reason is set on the final yield
        """
        user_message = self.test_case.first_message or "喂？"
        max_rounds = self.test_case.max_rounds or 50
        actual_rounds = 0

        for round_num in range(1, max_rounds + 1):
            actual_rounds = round_num

            # Record user (sparring) message
            self.conversation.append({"role": "user", "content": user_message})

            # Send to agent
            agent_reply, agent_ended = await self.agent_client.send_message(user_message)

            # Record agent reply (skip empty hangup replies)
            if agent_reply:
                self.conversation.append({"role": "assistant", "content": agent_reply})

            # Check: agent end signal
            if agent_ended:
                yield self.conversation, "agent_hangup", actual_rounds
                return

            # Check: max rounds reached
            if round_num >= max_rounds:
                yield self.conversation, "max_rounds", actual_rounds
                return

            # Generate next user message via sparring LLM
            next_message = await self._generate_next_message()

            # Check: sparring model signals end
            if END_MARKER in next_message:
                yield self.conversation, "sparring_end", actual_rounds
                return

            # Yield intermediate state (conversation ongoing)
            yield self.conversation, None, actual_rounds

            user_message = next_message

        yield self.conversation, "max_rounds", actual_rounds

    async def run(self) -> tuple[list[dict], str, int]:
        """Run the sparring conversation loop (compatibility wrapper).

        Returns:
            tuple: (conversation, termination_reason, actual_rounds)
        """
        conversation, termination_reason, actual_rounds = None, "max_rounds", 0
        async for conversation, termination_reason, actual_rounds in self.run_iter():
            pass
        return conversation or [], termination_reason or "max_rounds", actual_rounds

    async def _generate_next_message(self) -> str:
        # Swap roles: the sparring LLM *is* the assistant generating user messages,
        # so agent replies should appear as "user" and sparring messages as "assistant".
        # Without this swap, conversations ending with an assistant message cause many
        # models to return empty content.
        swapped = []
        for msg in self.conversation:
            role = "assistant" if msg["role"] == "user" else "user"
            swapped.append({"role": role, "content": msg["content"]})

        kwargs: dict = {
            "messages": swapped,
            "system_prompt": self.persona_prompt,
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens

        # Retry once if LLM returns empty (e.g. think-tag-only response)
        for _attempt in range(2):
            result = await self.llm.chat(**kwargs)
            if result.strip():
                return result
        return "嗯，请继续"
