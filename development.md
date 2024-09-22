# Microbe Bingo server setup

These are instructions for developers. If you want to make normal use of the bot, see [microbebingo.org](https://microbebingo.org/).

---

## Setting up the twitch account

1. Create a twitch account.
1. Verify your email.
1. Add a phone number.

	Not to be confused with setting 2FA.

	This is so that the bot is able to send messages in channels that require it.

	Some channels might require other things such as having a twitch account for a while, having followed for a while, or being a subscriber.

1. Set up 2FA.

	This is needed to so that you can create a Twitch Extension later.

1. Block whispers from strangers.

	So as to make sure people use email to contact you.

1. Disable receiving emails from twitch.

	Otherwise twitch will spam you.

1. Set profile picture.
1. Set channel bio.
1. Set profile accent color.
1. Set profile banner picture.
1. Set channel panels with a card example and instructions to enable the bot.
1. Set username color.
1. Set username capitalization.

	Twitch doesn't respect the capitalization you used on sign up, so fix it now.

1. Set suggested channels.

	So as to display some of the twitch microscopists.

1. Register a twitch application at the developer console: https://dev.twitch.tv/console/apps

		Name: Microbe Bingo
		OAuth Redirect URLs: https://microbebingo.org/myendpoint
		Category: Chat Bot
		Client Type: Confidential

	The Twitch Application doesn't need to be set with the same account that will be chatting, but I prefer it this way.

1. Take note of the Client ID and the Client Secret that will appear on the screen.

## Getting the first access and refresh tokens

Using your CHATBOT ACCOUNT, open in the browser:

	https://id.twitch.tv/oauth2/authorize?response_type=code&client_id=...&force_verify=true&scope=chat:read+chat:edit+clips:edit&redirect_uri=https://microbebingo.org/myendpoint

Once you authorize it, you will be redirected and the URL will contain `code` value.
(it may take a little bit, as you have to wait for the redirection fail because there's noone listening on the other side. you can look in the page source if you don't want to wait)

Now ask twitch for an access token using it:

	curl -X POST 'https://id.twitch.tv/oauth2/token' -H 'Content-Type: application/x-www-form-urlencoded' -d 'client_id=...&client_secret=...&code=...&grant_type=authorization_code&redirect_uri=https://microbebingo.org/myendpoint'

Example response:

	{"access_token":"...","expires_in":14531,"refresh_token":"...","scope":["chat:edit","chat:read"],"token_type":"bearer"}

Take note of the access token and the refresh token.

## Setting up the VM in GCP

Here is how I set up my VM:

1. Create a network:

		gcloud compute networks create mynetwork --subnet-mode=custom --mtu=1460 --bgp-routing-mode=regional

1. Configure the firewall:

		gcloud compute --project=yourprojectname firewall-rules create myrules --direction=INGRESS --priority=1000 --network=mynetwork --action=ALLOW --rules=tcp:22,tcp:80,tcp:443,udp:443 --source-ranges=0.0.0.0/0
		gcloud compute --project=yourprojectname firewall-rules create myrules-ipv6 --direction=INGRESS --priority=1000 --network=mynetwork --action=ALLOW --rules=tcp:22,tcp:80,tcp:443,udp:443 --source-ranges=::/0

1. Create a subnet:

		gcloud compute networks subnets create mysubnet --range=192.168.0.0/24 --stack-type=IPV4_IPV6 --ipv6-access-type=EXTERNAL --network=mynetwork --region=us-east1

1. Create and start the VM:

		gcloud compute instances create myvm \
			--zone=us-east1-b \
			--machine-type=e2-micro \
			--network-interface=ipv6-network-tier=PREMIUM,network-tier=PREMIUM,stack-type=IPV4_IPV6,subnet=mysubnet \
			--metadata=ssh-keys=dan:ssh-ed25519\ AAAAC3NzaC1lZDI1NTE5AAAAIIT6CJhr7CK\+goio66fB6hGl4EhgNlZgFxatGqUkhr2R\ dan \
			--maintenance-policy=MIGRATE \
			--provisioning-model=STANDARD \
			--no-service-account \
			--no-scopes \
			--tags=http-server,https-server \
			--create-disk=auto-delete=yes,boot=yes,device-name=mybootdisk,image-family=projects/debian-cloud/global/images/debian-12,mode=rw,size=10,type=projects/yourprojectname/zones/us-east1-b/diskTypes/pd-standard \
			--shielded-secure-boot \
			--shielded-vtpm \
			--shielded-integrity-monitoring \
			--labels=goog-ec-src=vm_add-gcloud \
			--reservation-affinity=any

	The important bit it to use no-service-account and no-scopes.

	In this example, a debian 12 boot disk image is used. By the time you read this, you will probably want a more updated image.

	Get one from `gcloud compute images list | grep debian`

	In this case I used `image-family`. The one you might get from the GUI might just be image

	These settings set up a free tier gcp vm.

	Here, we set our ssh key. Google will create a user for you based on this username.

1. Find out the public ipv4 assigned to the vm:

		gcloud compute instances list

1. Make it static so that we can safely add it as a DNS record later:

		gcloud compute addresses create my-addr-1 --addresses=<vm public ip> --region=us-east1

## Configuring the domain at Cloudflare

1. Add A record.
1. Add www CNAME record.
1. Add a hi@microbebingo.org email to be routed to an email account of your choice.

	Tip: Create a gmail filter that puts a label on every email addressed to `*@microbebingo.org`. It makes it easier to spot when you receive a routed email instead of a regular email.

1. Modify the spf TXT record (created automatically after the last step) from `~all` to `-all`. (as we don't send emails from this domain)
1. Click the button to set up DNSSEC automatically.
1. Click the button to set up automatic https rewrite and the button to always use https. This is only so that the annoying box goes away.


## Setting up the debian system

1. On your local machine, set up an ssh host alias at `~/.ssh/config`:

		Host myvm
			User dan
			HostName microbebingo.org
			HostKeyAlias myvm
			
		Host myvmTmux
			User dan
			HostName microbebingo.org
			HostKeyAlias myvm
			RequestTTY yes
			RemoteCommand tmux new-session -A -s mytmuxsession

1. Connect for the first time:

		ssh myvm

1. Type 'yes' to accept the fingerprint offered by the server for the first time.
1. Now you should be logged in the remote machine! Let's continue with the setup. This should take a minute..

		# in case you mindlessly paste this and something breaks silently
		set -e
		
		# disable man pages refreshing because it's slow and hangs
		sudo systemctl disable man-db.timer && sudo systemctl stop man-db.timer
		echo "set man-db/auto-update false" | sudo debconf-communicate && sudo dpkg-reconfigure man-db --frontend=noninteractive
		
		# make logs more readable by using your timezone
		sudo timedatectl set-timezone America/Sao_Paulo
		
		# reserve our id before installing more software
		sudo addgroup --gid 444 unpriv
		sudo adduser --uid 444 --gid 444 --disabled-password --gecos "" unpriv
		
		# install dependencies and goodies
		sudo apt update ; sudo apt upgrade -y
		sudo apt install -y docker.io rsync tmux htop fish neofetch screenfetch
		
		# save writing "sudo" every time you invoke docker
		sudo usermod -aG docker $USER
		
		# shut perl warnings up
		echo "LC_ALL=C.utf8" | sudo tee -a /etc/default/locale
		
		# allow nonroot to bind to port 80
		echo net.ipv4.ip_unprivileged_port_start=0 | sudo tee -a /etc/sysctl.conf
		
		# needed when caddy runs as nonroot
		echo net.core.rmem_max=7500000 | sudo tee -a /etc/sysctl.conf
		echo net.core.wmem_max=7500000 | sudo tee -a /etc/sysctl.conf
		sudo sysctl --system
		
		# set shell and remove ugly prompt
		sudo chsh -s /usr/bin/fish $USER
		fish -c "set -U fish_greeting ''"
		
		# make sure everything is good
		sudo reboot

## Setting up the containers

1. Create a `credentials` file to store your secrets. They'll be passed as env vars to the containers. Use this format:

		CLIENT_ID=...
		CLIENT_SECRET=...

		CARDDEALER_REFRESH_TOKEN=...
		CARDDEALER_ACCESS_TOKEN=...

		WATCHDOG_REFRESH_TOKEN=...
		WATCHDOG_ACCESS_TOKEN=...

1. Create a `entered_channels.txt` file to store the channels to be connected to upon startup. Use one twitch username per line. Entries will be added/removed from this file as users use the `!bingoenter`/`!bingoleave` commands.

1. Copy files over and set their permissions:

		rsync --verbose --progress --recursive --exclude ".git" /your_local_machine/microbebingo myvm:"~"
		ssh myvm "~/microbebingo/permissions_setter.sh"

1. ssh in using the `myvmTmux` alias when you want to get a shell. Use the `myvm` alias otherwise.

		ssh myvmTmux
		cd ~/microbebingo

1. Start the containers!

		./docker-compose up

1. Check if everything is working: Go to https://www.twitch.tv/popout/dogelectus/chat?popout= and open a card png image.

	(you might not see the first message if one container logs into twitch before the other. a little race condition I might fix some time🤷)

