FROM freqtradeorg/freqtrade:stable

# Switch to root for installations
USER root

WORKDIR /freqtrade

# Install additional Python dependencies
COPY services/freqtrade-integration/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create directories
RUN mkdir -p /freqtrade/user_data/strategies \
             /freqtrade/user_data/data \
             /freqtrade/user_data/logs

# Copy strategy and configuration
COPY services/freqtrade-integration/strategy.py /freqtrade/user_data/strategies/AIEnhancedStrategy.py
COPY services/freqtrade-integration/config.json /freqtrade/config.json
COPY services/freqtrade-integration/api.py /freqtrade/api.py

# Copy entrypoint script
COPY services/freqtrade-integration/entrypoint.sh /freqtrade/entrypoint.sh
RUN chmod +x /freqtrade/entrypoint.sh

# Set ownership to ftuser
RUN chown -R ftuser:ftuser /freqtrade

# Switch back to ftuser
USER ftuser

# Expose ports
EXPOSE 8080 8008

ENTRYPOINT ["/freqtrade/entrypoint.sh"]

