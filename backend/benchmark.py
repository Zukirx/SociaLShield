import asyncio
import time
import httpx

async def fetch(client, i):
    start = time.time()
    try:
        response = await client.post("http://127.0.0.01:8000/analyze", json={}, timeout=10.0)
        end = time.time()
        return end - start, response.status_code
    except Exception as e:
        end = time.time()
        return end - start, str(e)

async def main():
    print("Simulating heavy concurrent request batches to FastAPI...")
    num_requests = 100
    async with httpx.AsyncClient() as client:
        start_total = time.time()
        tasks = [fetch(client, i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        end_total = time.time()
        
    successful = [r[0] for r in results if isinstance(r[1], int) and r[1] == 200]
    errors = [r for r in results if not (isinstance(r[1], int) and r[1] == 200)]
    
    if successful:
        avg_latency = sum(successful) / len(successful)
        max_latency = max(successful)
        print(f"\n--- Benchmark Results ---")
        print(f"Total Requests: {num_requests}")
        print(f"Successful: {len(successful)}")
        print(f"Errors: {len(errors)}")
        print(f"Average Latency: {avg_latency*1000:.2f} ms")
        print(f"Max Latency: {max_latency*1000:.2f} ms")
        print(f"Total Time for Batch: {end_total - start_total:.2f} s")
        if avg_latency < 0.120:
            print("\nSUCCESS: Maintained sub-120ms response latency under heavy concurrent request batches.")
        else:
            print(f"\nWARNING: Average latency {avg_latency*1000:.2f}ms is above 120ms threshold.")
    else:
        print("All requests failed. Is the server running?")
        print(f"Sample error: {errors[0] if errors else 'None'}")

if __name__ == "__main__":
    asyncio.run(main())
