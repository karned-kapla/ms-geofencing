# ms-geofencing

Le service est prévu pour tourner sur un Raspberry.

## lancement du service

```bash
sudo vim /etc/systemd/system/geofencing.service
```
y placer le contenu du fichier geofencing.service

```bash
curl -L "https://github.com/opencv/opencv/raw/master/samples/data/vtest.avi" -o test_video.avi
```

