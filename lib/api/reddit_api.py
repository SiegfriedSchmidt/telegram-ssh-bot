import aiohttp
import asyncio


# r/{subreddit}/comments/{id}/{name_of_post}.json?sort={sort by}

async def get_subreddit(subreddit: str):
    params = {
        "sort": "hot",
        "limit": 6
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.reddit.com/r/{subreddit}.json", params=params) as resp:
            print(resp.status)
            print(resp.reason)
            print(await resp.text())
            return (await resp.json())["data"]


# async def get_media_type(data: dict) -> RedditMediaType:
#     if data['is_gallery']:
#         return RedditMediaType.gallery
#     elif data['is_video']:
#         return RedditMediaType.video

async def main():
    data = await get_subreddit("desmos")
    print(data.keys())
    children = data["children"]
    print(len(children))
    print(children[0]["data"].keys())
    print(children[0]["data"]["media_embed"].keys())

    for child in children:
        child_data = child["data"]
        print(child_data)
        print(
            child_data['name'],
            child_data['subreddit'],
            child_data['title'],
            child_data['stickied'],
            child_data['author_fullname'],
            # child_data['selftext'],
            child_data['ups'],
            child_data['upvote_ratio'],
            child_data['is_video'],
            child_data['url'],
            child_data.get('media', None),
            sep='\n'
        )
        print('-' * 20)


if __name__ == '__main__':
    asyncio.run(main())
