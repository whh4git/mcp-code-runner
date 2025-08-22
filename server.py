import asyncio
import re
from typing import Annotated, Any
from fastmcp import Client, Context, FastMCP
from fastmcp.exceptions import ToolError


# 1. Create the server
mcp = FastMCP(name="code-runner", instructions="Codr Runner MCP Server")
system_args: dict[str] = dict()


class ExecuteException(Exception):
    pass


# 2. Add a tool
async def execute(
    cmd: list[str],
    env: dict[str, Any] = dict(),
    timeout: float = 300,
    name: str = None,
    image: str = None,
) -> str:
    """
    Execute code in a container or virtual machine environment.
    """

    name = system_args.get("name", name)
    image = system_args.get("image", image)
    if name is None and image is None:
        raise ToolError("Must set up a image or container.")

    async def __cli_run(
        cmd: list[str],
        timeout: float = 60,
    ) -> tuple[int, bytes, bytes]:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout)
        exit_code = await proc.wait()

        return exit_code, stdout, stderr

    envs = []
    for k, v in env.items():
        envs.append("--env")
        envs.append(f"{k}={v}")

    if name is None:
        cmd = ["docker", "run", *envs, "--rm", image] + cmd
    else:
        start_cmd = ["docker", "start", name]
        exit_code, _, stderr = await __cli_run(start_cmd, 10)
        if exit_code != 0:
            err = stderr.decode() if stderr else "failed to start containers"
            raise ExecuteException(err)

        cmd = ["docker", "exec", *envs, name] + cmd

    try:
        exit_code, stdout, stderr = await __cli_run(cmd, timeout)

        if exit_code != 0:
            raise ExecuteException(stderr.decode())
        return stdout.decode()

    except TimeoutError:
        raise ToolError("TimeoutError")


@mcp.tool()
async def python_execute(
    ctx: Context,
    code: Annotated[str, "The Python code to execute"],
    env: Annotated[dict[str, Any], "Set environment variables.(Optional)"] = dict(),
    timeout: Annotated[float, "Timeout in seconds (default: 300)"] = 300,
) -> str:
    """
    Execute Python code in a container or virtual machine environment.
    You will get results from stdout.
    Supports most Python standard library and scientific packages.
    The code will be executed with Python 3.11 or higher.
    """

    # cmd = ["uv", "run"]
    cmd = ["python", "-q", "-u", "-I", "-c", code]

    return await execute(cmd, env=env, timeout=timeout)


@mcp.tool()
async def bash_execute(
    ctx: Context,
    code: Annotated[str, "The bash code to execute."],
    env: Annotated[dict[str, Any], "Set environment variables.(Optional)"] = dict(),
    timeout: Annotated[float, "Timeout in seconds.(Optional)"] = 300,
) -> str:
    """
    Execute bash code in a container or virtual machine environment.
    """

    cmd = ["bash", "-c", code]
    return await execute(cmd, env=env, timeout=timeout)


@mcp.tool()
async def get_python_modules(
    timeout: Annotated[float, "Timeout in seconds (default: 15)"] = 15,
) -> list[str]:
    """Provides the python available third-party modules."""

    cmds = [
        ["apt-mark", "showmanual", "python3-*"],
        ["pacman", "-Qe"],
    ]
    for cmd in cmds:
        try:
            result = (await execute(cmd, timeout=timeout)).split("\n")
            result = (re.search(r"^python3?-(\S+)\s*.*$", l, re.I) for l in result)
            result = (r[1] for r in result if not (r is None))
            return list(result)
        except ExecuteException:
            pass

    return ToolError("not found")


async def test_weather_operations():
    # Pass server directly - no deployment needed
    async with Client(mcp) as client:
        # Test tool execution
        global system_args

        system_args = {"name": "6eb5d7c81542"}
        print(system_args)
        result = await client.call_tool(
            "python_execute",
            {"code": "print('hello world')", "timeout": 16},
        )
        print(result.data)
        assert result.data == "hello world\n"

        result = await client.call_tool(
            "python_execute",
            {"code": "print('hello world')", "timeout": 16},
        )
        print(result.data)
        assert result.data == "hello world\n"

        system_args = {"image": "kali-code-runner"}
        result = await client.call_tool(
            "bash_execute",
            {"code": "echo 'hello world'", "timeout": 16},
        )
        print(result.data)


# 5. Make the server runnable
if __name__ == "__main__":
    asyncio.run(test_weather_operations())
