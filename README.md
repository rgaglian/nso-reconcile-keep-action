# NSO Reconcile Keep Action

Tested with NSO 5.8

This is a package that I created to show how we can create actions that limit NSO default service actions and expose them to some users.

In this case, we want to expose "service re-deploy reconcile" but not given the option for "discard-non-service-config"

Note: I assumed that "deviation" would not work with NSO native actions but I have not test that option

Here is how it works:

1- clone this repository
2- compile the package: % make -C packages/reconcile-keep/src clean all
3- perform package re-deploy
4- Add NACM rule to deny re-deploy and permit the new actions:
```
set nacm rule-list oper group [ oper ]
set nacm rule-list oper rule rule_reconcile path /l3vpn:vpn/l3vpn:l3vpn/reconcile-keep action permit
set nacm rule-list oper rule rule_redeploy path /l3vpn:vpn/l3vpn:l3vpn/re-deploy action deny
set nacm rule-list oper rule rule_reconcile_full path /l3vpn:vpn/l3vpn:l3vpn/reconcile-keep-full action permit
```
5- login as "oper"
  Note: You need to do it via SSH or WebUI
6- try to execute the commands:
```
oper@ncs> request vpn l3vpn test_tel
Possible completions:
  check-sync          - Check if device config is according to the service
  commit-queue        -
  deep-check-sync     - Check if device config is according to the service
  get-modifications   - Get the data this service created
  log                 -
  reactive-re-deploy  - Reactive re-deploy of service logic
  reconcile-keep      -
  reconcile-keep-full -
  un-deploy           - Undo the effects of the service
oper@ncs>
```
---> You can see that re-deploy is missing now but the new "reconcile-keep" are available.

So, there are two options:
  reconcile-keep      - In this case the number of options were limited
  reconcile-keep-full - This is basically a copy of re-deploy but without the "bad input"

