# Author Akshat Sharma

import argparse
import datetime
import os
import time
import json
import math
import jwt
import paho.mqtt.client as mqtt

import random

def create_jwt(project_id, private_key_file, algorithm):
    """Creates a JWT (https://jwt.io) to establish an MQTT connection.
        Args:
         project_id: The cloud project ID this device belongs to
         private_key_file: A path to a file containing either an RSA256 or
                 ES256 private key.
         algorithm: The encryption algorithm to use. Either 'RS256' or 'ES256'
        Returns:
            An MQTT generated from the given project_id and private key, which
            expires in 20 minutes. After 20 minutes, your client will be
            disconnected, and a new JWT will have to be generated.
        Raises:
            ValueError: If the private_key_file does not contain a known key.
        """

    token = {
            # The time that the token was issued at
            'iat': datetime.datetime.utcnow(),
            # The time the token expires.
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            # The audience field should always be set to the GCP project id.
            'aud': project_id
    }

    # Read the private key file.
    with open(private_key_file, 'r') as f:
        private_key = f.read()

    print('Creating JWT using {} from private key file {}'.format(
            algorithm, private_key_file))

    return jwt.encode(token, private_key, algorithm=algorithm)


def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return '{}: {}'.format(rc, mqtt.error_string(rc))


def on_connect(unused_client, unused_userdata, unused_flags, rc):
    """Callback for when a device connects."""
    print('on_connect', error_str(rc))


def on_disconnect(unused_client, unused_userdata, rc):
    """Paho callback for when a device disconnects."""
    print('on_disconnect', error_str(rc))


def on_publish(unused_client, unused_userdata, unused_mid):
    """Paho callback when a message is sent to the broker."""
    print('on_publish')


def parse_command_line_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=(
            'Example Google Cloud IoT Core MQTT device connection code.'))
    parser.add_argument(
            '--project_id',
            default=os.environ.get('GOOGLE_CLOUD_PROJECT'),
            help='GCP cloud project name')
    parser.add_argument(
            '--registry_id', required=True, help='Cloud IoT Core registry id')
    parser.add_argument(
            '--device_id', required=True, help='Cloud IoT Core device id')
    parser.add_argument(
            '--private_key_file',
            required=True, help='Path to private key file.')
    parser.add_argument(
            '--algorithm',
            choices=('RS256', 'ES256'),
            required=True,
            help='Which encryption algorithm to use to generate the JWT.')
    parser.add_argument(
            '--cloud_region', default='us-central1', help='GCP cloud region')
    parser.add_argument(
            '--ca_certs',
            default='roots.pem',
            help=('CA root from https://pki.google.com/roots.pem'))
    parser.add_argument(
            '--num_messages',
            type=int,
            default=100,
            help='Number of messages to publish.')
    parser.add_argument(
            '--message_type',
            choices=('event', 'state'),
            default='event',
            required=True,
            help=('Indicates whether the message to be published is a '
                  'telemetry event or a device state message.'))
    parser.add_argument(
            '--mqtt_bridge_hostname',
            default='mqtt.googleapis.com',
            help='MQTT bridge hostname.')
    parser.add_argument(
            '--mqtt_bridge_port',
            default=8883,
            type=int,
            help='MQTT bridge port.')

    return parser.parse_args()


def main():
    args = parse_command_line_args()

    # Create our MQTT client. The client_id is a unique string that identifies
    # this device. For Google Cloud IoT Core, it must be in the format below.
    client = mqtt.Client(
            client_id=('projects/{}/locations/{}/registries/{}/devices/{}'
                       .format(
                               args.project_id,
                               args.cloud_region,
                               args.registry_id,
                               args.device_id)))

    # With Google Cloud IoT Core, the username field is ignored, and the
    # password field is used to transmit a JWT to authorize the device.
    client.username_pw_set(
            username='unused',
            password=create_jwt(
                    args.project_id, args.private_key_file, args.algorithm))

    # Enable SSL/TLS support.
    client.tls_set(ca_certs=args.ca_certs)

    # Register message callbacks. https://eclipse.org/paho/clients/python/docs/
    # describes additional callbacks that Paho supports. In this example, the
    # callbacks just print to standard out.
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect

    # Connect to the Google MQTT bridge.
    client.connect(args.mqtt_bridge_hostname, args.mqtt_bridge_port)

    # Start the network loop.
    client.loop_start()

    # Publish to the events or state topic based on the flag.
    sub_topic = 'events' if args.message_type == 'event' else 'state'

    mqtt_topic = '/devices/{}/{}'.format(args.device_id, sub_topic)

    random.seed(args.device_id)  # A given device ID will always generate
                                 # the same random data

    simulated_temp      = 45    + random.random() * 20
    simulated_temp_out  = 35    + random.random() * 10
    sim_pressure        = 1000  + random.random() * 25
    sim_hum             = 25    + random.random() * 30
    sim_hum_out         = 15    + random.random() * 30
    sim_uv              = 5     + random.random() * 10
    sim_irr             = 6     + random.random() * 10
    sim_smoist          = 50    + random.random() * 10
    sim_co2             = 430   + random.random() * 50
    sim_ch4             = 1900  + random.random() * 200
    sim_n20             = 330   + random.random() * 100
    sim_cfc             = 900   + random.random() * 300



    if random.random() > 0.5:
        temperature_trend = +1     # temps will slowly rise
    else:
        temperature_trend = -1     # temps will slowly fall

    # Publish num_messages mesages to the MQTT bridge once per second.
    for i in range(1, args.num_messages + 1):

        simulated_temp      = simulated_temp        + temperature_trend * random.normalvariate(0.01,0.005)
        simulated_temp_out  = simulated_temp_out    + temperature_trend * random.normalvariate(0.01,0.005)
        sim_pressure        = sim_pressure          + (1 if random.random() > 0.5 else -1) * random.normalvariate(0.1,0.01)
        sim_hum             = sim_hum               + (1 if random.random() > 0.5 else -1) * random.normalvariate(0.1,0.01)
        sim_hum_out         = sim_hum_out           - (1 if random.random() > 0.5 else -1) * random.normalvariate(0.1,0.01)
        sim_uv              = sim_uv                + (1 if random.random() > 0.5 else -1) * random.normalvariate(0.1,0.01)
        sim_irr             = sim_irr               + (1 if random.random() > 0.5 else -1) * random.normalvariate(0.1,0.01)
        sim_smoist          = sim_smoist            + (1 if random.random() > 0.5 else -1) * random.normalvariate(0.1,0.01)
        sim_co2             = sim_co2               + (1 if random.random() > 0.5 else -1) * random.normalvariate(0.1,0.01)
        sim_ch4             = sim_ch4               + (1 if random.random() > 0.5 else -1) * random.normalvariate(0.1,0.01)
        sim_n20             = sim_n20               + (1 if random.random() > 0.5 else -1) * random.normalvariate(0.1,0.01)
        sim_cfc             = sim_cfc               + (1 if random.random() > 0.5 else -1) * random.normalvariate(0.1,0.01)

        g_score = ((simulated_temp - simulated_temp_out)^3/500 + math.sqrt(math.sqrt(sim_ch4 + sim_co2 + sim_n20 + sim_cfc)) 
            - 10 * (sim_smoist + sim_irr) + sim_uv )/(sim_pressure + (sim_hum - sim_hum_out))



        payload = {"timestamp": int(time.time()), "device": args.device_id,
         "Temp In": simulated_temp,
         "Temp Out": simulated_temp_out,
         "Pressure": sim_pressure,
         "Humidity In": sim_hum,
         "Humidity Out": sim_hum_out,
         "UV Index": sim_uv,
         "Solar Irradiance": sim_irr,
         "Soil Moisture": sim_smoist,
         "Carbon Dioxide ppb": sim_co2,
         "Methan ppb": sim_ch4,
         "Nitrous Oxide ppb": sim_n20,
         "CFC ppb": sim_cfc,
         "G - Index": g_score}
        print('Publishing message {} of {}: \'{}\''.format(
                i, args.num_messages, payload))
        jsonpayload =  json.dumps(payload,indent=4)
        # Publish "jsonpayload" to the MQTT topic. qos=1 means at least once
        # delivery. Cloud IoT Core also supports qos=0 for at most once
        # delivery.
        client.publish(mqtt_topic, jsonpayload, qos=1)

        # Send events every second. State should not be updated as often
        time.sleep(1 if args.message_type == 'event' else 5)

    # End the network loop and finish.
    client.loop_stop()
    print('Finished.')


if __name__ == '__main__':
    main()
