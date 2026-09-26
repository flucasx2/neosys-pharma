# Déploiement de NeoSys Pharma sur AWS EC2

Cette procédure publie l'application à l'adresse
`https://demo.neosysconsulting.com/encaissement` avec une authentification
obligatoire avant l'accès aux pages et à l'API.

## 1. Instance EC2

Configuration conseillée pour la démonstration :

- région : Afrique (Le Cap), `af-south-1` ;
- image : Ubuntu Server 24.04 LTS ;
- type : `t3.micro` ;
- disque : 12 Gio GP3 chiffré ;
- adresse IPv4 Elastic IP associée à l'instance ;
- règle SSH 22 limitée à votre adresse IP ;
- règles HTTP 80 et HTTPS 443 ouvertes au public.

Ne jamais ouvrir directement le port 8000 dans le groupe de sécurité.

## 2. Transfert depuis Windows PowerShell

```powershell
scp -i .\votre-cle.pem .\NeoSys_Pharma_v1.8.0.zip ubuntu@ADRESSE_ELASTIC_IP:/tmp/
ssh -i .\votre-cle.pem ubuntu@ADRESSE_ELASTIC_IP
```

## 3. Préparation du serveur

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx certbot python3-certbot-nginx unzip
sudo adduser --system --group --home /opt/neosys-pharma neosys
sudo mkdir -p /opt/neosys-pharma /var/lib/neosys-pharma
sudo unzip /tmp/NeoSys_Pharma_v1.8.0.zip -d /opt/neosys-pharma
sudo python3 -m venv /opt/neosys-pharma/venv
sudo /opt/neosys-pharma/venv/bin/pip install --upgrade pip
sudo /opt/neosys-pharma/venv/bin/pip install /opt/neosys-pharma/NeoSys_Pharma
sudo chown -R neosys:neosys /opt/neosys-pharma /var/lib/neosys-pharma
```

## 4. Secrets et authentification

Générer deux valeurs différentes :

```bash
openssl rand -base64 24
openssl rand -hex 32
```

Copier le modèle puis remplacer le mot de passe et le secret :

```bash
sudo cp /opt/neosys-pharma/NeoSys_Pharma/deploy/ec2/neosys-pharma.env.example /etc/neosys-pharma.env
sudo nano /etc/neosys-pharma.env
sudo chmod 600 /etc/neosys-pharma.env
```

Ne jamais transmettre le contenu du fichier `/etc/neosys-pharma.env` et ne
jamais l'ajouter à une archive ou à Git.

## 5. Service FastAPI

```bash
sudo cp /opt/neosys-pharma/NeoSys_Pharma/deploy/ec2/neosys-pharma.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now neosys-pharma
sudo systemctl status neosys-pharma --no-pager
curl http://127.0.0.1:8000/api/v1/health
```

## 6. Nginx

```bash
sudo cp /opt/neosys-pharma/NeoSys_Pharma/deploy/ec2/nginx-demo.neosysconsulting.com.conf /etc/nginx/sites-available/demo.neosysconsulting.com
sudo ln -s /etc/nginx/sites-available/demo.neosysconsulting.com /etc/nginx/sites-enabled/demo.neosysconsulting.com
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 7. DNS

Dans la zone DNS existante de `neosysconsulting.com`, créer :

- type : `A` ;
- nom : `demo` ;
- cible : l'adresse Elastic IP de l'instance ;
- TTL : automatique ou 300 secondes.

Si Cloudflare gère le DNS, laisser temporairement le proxy désactivé pendant
l'émission initiale du certificat.

## 8. HTTPS

Après propagation du DNS et après avoir vérifié que
`http://demo.neosysconsulting.com` répond :

```bash
sudo certbot --nginx -d demo.neosysconsulting.com
sudo certbot renew --dry-run
```

Choisir la redirection automatique de HTTP vers HTTPS.

## 9. Contrôles finaux

1. Ouvrir `https://demo.neosysconsulting.com/encaissement` en navigation privée.
2. Vérifier que la page de connexion apparaît avant l'encaissement.
3. Vérifier qu'un mauvais mot de passe est refusé.
4. Se connecter et vérifier la redirection vers `/encaissement`.
5. Tester préparation, validation, encaissement et déconnexion.
6. Vérifier que `https://demo.neosysconsulting.com/api/v1/catalogue/articles`
   renvoie `401` sans session.

## 10. Commandes de diagnostic

```bash
sudo systemctl status neosys-pharma --no-pager
sudo journalctl -u neosys-pharma -n 100 --no-pager
sudo nginx -t
sudo tail -n 100 /var/log/nginx/error.log
```
