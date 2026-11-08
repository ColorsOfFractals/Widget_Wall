import asyncio
from winrt.windows.devices.geolocation import (
    Geolocator,
    GeolocationAccessStatus
)

async def main():
    print("\n--- REQUEST WINDOWS LOCATION ACCESS ---")

    status = await Geolocator.request_access_async()
    print("Access status:", status)

    if status != GeolocationAccessStatus.ALLOWED:
        print("Location access unavailable or denied.")
        return

    print("\n--- REQUEST POSITION ---")

    locator = Geolocator()
    locator.desired_accuracy_in_meters = 1000

    try:
        position = await asyncio.wait_for(
            locator.get_geoposition_async(),
            timeout=15
        )

        coordinate = position.coordinate
        print("Position obtained: YES")
        print("Accuracy (meters):",
              coordinate.accuracy)

    except Exception as error:
        print("Position obtained: NO")
        print("Error:", type(error).__name__, str(error))

asyncio.run(main())