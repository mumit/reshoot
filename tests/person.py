"""For the tests: a stand-in for a person using Chrome, through DevTools input events (trusted, like real ones)."""
import asyncio, json


async def center(page, sel):
    for _ in range(50):
        r = await page.run(f"const e = document.querySelector({json.dumps(sel)}); if (!e) return null;"
                           " const b = e.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]")
        if r:
            return r
        await asyncio.sleep(0.1)
    raise AssertionError(f"nothing matches {sel}")


async def click(page, sel):
    x, y = await center(page, sel)
    await page.cmd("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
    for kind in ("mousePressed", "mouseReleased"):
        await page.cmd("Input.dispatchMouseEvent", type=kind, x=x, y=y, button="left", clickCount=1)
    await asyncio.sleep(0.3)


async def type(page, text):
    for ch in text:
        await page.cmd("Input.insertText", text=ch)
        await asyncio.sleep(0.03)
    await asyncio.sleep(0.3)


async def enter(page):
    for kind in ("keyDown", "keyUp"):
        await page.cmd("Input.dispatchKeyEvent", type=kind, key="Enter", code="Enter", windowsVirtualKeyCode=13,
                       **({"text": "\r"} if kind == "keyDown" else {}))
    await asyncio.sleep(0.3)


async def backspace(page, times):
    for _ in range(times):
        for kind in ("rawKeyDown", "keyUp"):
            await page.cmd("Input.dispatchKeyEvent", type=kind, key="Backspace", code="Backspace", windowsVirtualKeyCode=8)
        await asyncio.sleep(0.03)
    await asyncio.sleep(0.3)


async def click_at(page, x, y):
    await page.cmd("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
    for kind in ("mousePressed", "mouseReleased"):
        await page.cmd("Input.dispatchMouseEvent", type=kind, x=x, y=y, button="left", clickCount=1)
    await asyncio.sleep(0.3)


async def clearing_tour(page):
    """Searches, clicks the empty page, comes back and clears the search with Backspace, then searches again.
    Typing in one field with nothing else between is one run, so the steps are split by other clicks."""
    await asyncio.sleep(1.5)
    await click(page, "#q"); await type(page, "bread")
    await click_at(page, 30, 700)  # the page's background: not an action
    await click(page, "#text")
    await click(page, "#q"); await backspace(page, 5)
    await click(page, "#text")
    await click(page, "#q"); await type(page, "tap")
    await asyncio.sleep(0.8)


async def notes_tour(page):
    """Visits the About page and back, adds a note with Enter, then searches for it. (Notes live only in the page,
    so a page load would forget the note: it's added after the visit.)"""
    await asyncio.sleep(1.5)
    await click(page, "#about"); await asyncio.sleep(1.0)
    await click(page, "#back"); await asyncio.sleep(1.0)
    await click(page, "#text"); await type(page, "Buy stamps"); await enter(page)
    await asyncio.sleep(1.0)
    await click(page, "#q"); await type(page, "stamps")
    await asyncio.sleep(0.8)
