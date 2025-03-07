# ms-geofencing

Le service est prévu pour tourner sur un Raspberry.

## Installation de docker sur le raspberry
```sh
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

## Lancement du service
```sh
docker build -t intrusion-detection .
docker run --rm --name intrusion_service intrusion-detection
```

```sh 
sudo crontab -e
```

Ajouter : @reboot docker start intrusion_service
