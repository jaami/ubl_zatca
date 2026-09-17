FROM python:3.9-slim

# Install necessary packages
RUN apt update && \
    apt install -y nano less jq gcc g++ && \
    apt-get clean;


# Copy JDK 11 from your local machine
COPY /jdk11 /app/jdk11

# Set JAVA_HOME and update PATH
ENV JAVA_HOME /app/jdk11
ENV PATH="$PATH:/app/jdk11:/app/jdk11/bin"

# Set FATOORA_HOME and SDK_CONFIG environment variables
ENV FATOORA_HOME /app/ZatcaSDK/Apps
ENV SDK_CONFIG /app/ZatcaSDK/Configuration

# Add FATOORA_HOME to PATH
ENV PATH="$PATH:$FATOORA_HOME"

WORKDIR /app

# Copy ZATCA SDK files and make install script executable
COPY --chmod=755 ZatcaSDK /app/ZatcaSDK
RUN chmod -R 755 /app/ZatcaSDK

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install JPype1
RUN pip install JPype1

COPY . .

# Make entrypoint script executable and set it as the entrypoint
COPY --chmod=755 entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
