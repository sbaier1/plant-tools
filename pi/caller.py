import asyncio
from aioesphomeapi import APIClient, APIConnectionError

# Define your ESPHome device details
ESPHOME_HOST = 'servocontrol.local'  # Replace with your device's IP address
ESPHOME_PORT = 6053  # Default API port, change if necessary
ESPHOME_PASSWORD = ''  # If no password is set, leave as an empty string

# Define the service and its variables
SERVICE_NAME = 'run_servo_relay_script'
VARIABLES = {'relay_high_duration': 1.5}  # Example duration in seconds

async def call_esphome_service():
    client = APIClient(ESPHOME_HOST, ESPHOME_PORT, ESPHOME_PASSWORD)

    try:
        await client.connect(login=True)
        services = await client.list_entities_services()
        print(services)
        # Find the correct service
        for service in services:
            if len(service) > 0 and service[0].name == SERVICE_NAME:
                print(f"Found service: {service[0].name}")
                # Call the service with the defined variables
                client.execute_service(service[0], VARIABLES)
                print(f"Service {SERVICE_NAME} called successfully with variables {VARIABLES}")
                break
        else:
            print(f"Service {SERVICE_NAME} not found on the device.")
    except APIConnectionError as e:
        print(f"Failed to connect to the ESPHome device: {e}")
    finally:
        await client.disconnect()

# Run the async function
if __name__ == '__main__':
    asyncio.run(call_esphome_service())
