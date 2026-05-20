Classroom Energy Monitoring and Visualization System

This repository contains the Python source code used for the thesis project Design of Energy Consumption Monitoring and Visualization System for Classrooms Based on Internet of Things.

The system uses a Raspberry Pi as the local edge node. The main functions include collecting occupancy and range data from a 24 GHz millimeter-wave radar through UART, collecting power, voltage, and current data from a TP-Link Tapo P110/P110M smart plug, publishing selected smart plug data through MQTT, writing processed measurements directly into InfluxDB, and visualizing the stored data later in Grafana.

#Files

·smart_plug_monitor.py: collects power, voltage, and current data from the TP-Link Tapo smart plug, publishes the data to MQTT, and writes the processed measurements into InfluxDB.
·radar_monitor.py: collects occupancy and range data from the 24 GHz millimeter-wave radar through UART and writes the processed measurements into InfluxDB.

Privacy Notice

Sensitive information such as Wi-Fi passwords, Tapo account details, smart plug IP addresses, and InfluxDB tokens have been removed or replaced with placeholders before publication.
