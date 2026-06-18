import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.models.models import Monitor

INITIAL_URLS = [
    "https://promptwars-week-3.vercel.app/",
    "https://cluster-adaptive-blood-report-analy.vercel.app/",
    "https://web-prog-project-weld.vercel.app/",
    "https://sreeansh-dash.netlify.app/",
    "https://enchanting-banoffee-6c5cf4.netlify.app/",
    "https://cs-sandbox.netlify.app/",
    "https://indianedgeanpr.netlify.app/"
]

def extract_name(url: str) -> str:
    # Basic logic to extract a readable name from URL
    name = url.replace("https://", "").replace("http://", "").split(".")[0]
    return name.title().replace("-", " ")

async def seed():
    async with async_session_maker() as session:
        for url in INITIAL_URLS:
            monitor = Monitor(
                name=extract_name(url),
                url=url,
                check_interval_seconds=120  # Default 2 minutes
            )
            session.add(monitor)
        
        await session.commit()
        print(f"Seeded {len(INITIAL_URLS)} monitors.")

if __name__ == "__main__":
    asyncio.run(seed())
