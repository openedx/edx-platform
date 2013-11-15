# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "precise32"
  config.vm.box_url = "http://files.vagrantup.com/precise32.box"

  config.vm.network :forwarded_port, guest: 8000, host: 9000
  config.vm.network :forwarded_port, guest: 8001, host: 9001

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  config.vm.network :private_network, ip: "192.168.10.40"

  nfs_setting = RUBY_PLATFORM =~ /darwin/ || RUBY_PLATFORM =~ /linux/
  config.vm.synced_folder ".", "/opt/edx/edx-platform", id: "vagrant-root", :nfs => nfs_setting
  config.vm.synced_folder "../themes", "/opt/edx/themes", id: "vagrant-theems", :nfs => nfs_setting
  # Make it so that network access from the vagrant guest is able to
  # use SSH private keys that are present on the host without copying
  # them into the VM.
  config.ssh.forward_agent = true

  config.vm.provider :virtualbox do |vb|
    # Use VBoxManage to customize the VM. For example to change memory:
    vb.customize ["modifyvm", :id, "--memory", "2048"]

    # This setting makes it so that network access from inside the vagrant guest
    # is able to resolve DNS using the hosts VPN connection.
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
  end

  config.vm.provision :shell, :path => "scripts/install-acceptance-req.sh"
  config.vm.provision :shell, :path => "scripts/vagrant-provisioning.sh"
end
