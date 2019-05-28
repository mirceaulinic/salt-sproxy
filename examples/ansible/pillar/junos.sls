proxy:
  proxytype: napalm
  driver: junos
  hostname: {{ opts.id | replace('.', '-') }}.salt-sproxy.digitalocean.cloud.tesuto.com
  username: test
  password: t35t1234
