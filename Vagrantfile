# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"
ENV['VAGRANT_DEFAULT_PROVIDER'] = 'virtualbox'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.define "sslangel-expiry-api" do |ubuntutest|
        ubuntutest.vm.hostname = "sslangel-expiry-api"
        ubuntutest.vm.box = "ubuntu/trusty64"
    end
end
