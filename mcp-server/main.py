import asyncio
import json

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tools.downloader import download_video, get_channel_related
from tools.frames import extract_frames

server = Server("ytdark-tools")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="download_video",
            description="Baixa um vídeo do YouTube com yt-dlp e retorna metadados e caminho local.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL do vídeo YouTube"},
                    "output_dir": {
                        "type": "string",
                        "description": "Diretório de saída (default: /tmp/ytdark)",
                        "default": "/tmp/ytdark",
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="get_channel_related",
            description="Retorna canais relacionados/featured de um canal YouTube via yt-dlp.",
            inputSchema={
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "Handle do canal (ex: @CasuallyFinance)",
                    }
                },
                "required": ["handle"],
            },
        ),
        Tool(
            name="extract_frames",
            description="Extrai N frames distribuídos de um vídeo com ffmpeg. Retorna lista de caminhos.",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_path": {"type": "string", "description": "Caminho local do vídeo"},
                    "n_frames": {
                        "type": "integer",
                        "description": "Número de frames a extrair (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["video_path"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "download_video":
            result = download_video(
                arguments["url"],
                arguments.get("output_dir", "/tmp/ytdark"),
            )
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "get_channel_related":
            result = get_channel_related(arguments["handle"])
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "extract_frames":
            paths = extract_frames(
                arguments["video_path"],
                arguments.get("n_frames", 10),
            )
            return [TextContent(type="text", text=json.dumps({"frames": paths}))]

        else:
            raise ValueError(f"Tool desconhecida: {name}")

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
