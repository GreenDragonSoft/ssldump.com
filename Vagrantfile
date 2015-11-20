# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"
ENV['VAGRANT_DEFAULT_PROVIDER'] = 'virtualbox'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.define "vagrant-ssldump" do |ubuntutest|
        ubuntutest.vm.hostname = "vagrant-ssldump"
        ubuntutest.vm.box = "ubuntu/trusty64"
    end
  
    config.vm.network :forwarded_port, guest: 80, host: 8080
    
    config.vm.synced_folder ".", "/opt/ssldump/ssldump-dev"

    config.vm.provision "shell",
      inline: "sudo apt-get update"

    config.vm.provision "ansible" do |ansible|
      ansible.playbook = "ansible-config/playbook.yml"
      ansible.inventory_path = "ansible-config/hosts"
      ansible.sudo = true
    end
end
