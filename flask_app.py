from flask import Flask, jsonify
import requests
import os
import logging

logging.basicConfig(level=logging.INFO)

# List of IPs to check (passed directly as a list)
ips = ["35.225.109.37", "34.170.246.185", "34.138.8.33", "35.231.18.216", "34.150.225.232", "35.245.223.75", "localhost"]

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    healthy = os.environ.get("HEALTHY") == "true"
    ip_block_data = {}  # Store each IP and its block number

    if healthy:
        try:
            block_numbers = []
            localhost_block = None
            
            for ip in ips:
                try:
                    response = requests.post(f"http://{ip}:9200", json={
                        "jsonrpc": "2.0",
                        "method": "quai_blockNumber",
                        "params": [],
                        "id": 1
                    }, timeout=5)
                    
                    # Parse the JSON response
                    data = response.json()
                    if "result" in data:
                        # Convert hex result to integer
                        block_number = int(data["result"], 16)
                        
                        # Store the block number with the IP
                        ip_block_data[ip] = block_number
                        
                        # Check if the response is from localhost
                        if ip == "localhost":
                            localhost_block = block_number
                        else:
                            block_numbers.append(block_number)
                except requests.RequestException:
                    logging.warning(f"Failed to get response from {ip}")
                    ip_block_data[ip] = None
                    continue
            
            # Check if we have at least one non-localhost block number and a localhost block
            if block_numbers and localhost_block is not None:
                highest_block = max(block_numbers)
                behind_by = highest_block - localhost_block

                
                # Log the values and difference
                logging.info("Highest block number from other nodes: %d", highest_block)
                logging.info("Current block number: %d", localhost_block)
                logging.info("This node is behind by: %d", behind_by)
                
                # Prepare the response with full details
                response_data = {
                    "status": "healthy" if behind_by < 100 else "unhealthy",
                    "current_height": localhost_block,
                    "max_height": highest_block,
                    "behind_by": behind_by,
                    "height_data": ip_block_data
                }
                
                return jsonify(response_data), 200 if behind_by < 100 else 503
            else:
                # If we don't have necessary data, mark as unhealthy
                response_data = {
                    "status": "unhealthy",
                    "error": "No valid responses from other IPs or localhost block missing",
                    "ip_blocks": ip_block_data
                }
                return jsonify(response_data), 503

        except Exception as e:
            # Return unhealthy with error and IP data if an exception occurred
            logging.error("Health check failed: %s", e)
            response_data = {
                "status": "unhealthy",
                "error": str(e),
                "ip_blocks": ip_block_data
            }
            return jsonify(response_data), 503
    else:
        # Respond with unhealthy if HEALTHY is false
        response_data = {
            "status": "unhealthy",
            "error": "HEALTHY environment variable is set to false",
            "ip_blocks": ip_block_data
        }
        return jsonify(response_data), 503

if __name__ == "__main__":
    app.run()

