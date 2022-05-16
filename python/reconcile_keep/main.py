# -*- mode: python; python-indent: 4 -*-
import ncs
from ncs.application import Service
from ncs.dp import Action
import _ncs


# ---------------
# ACTIONS EXAMPLE
# ---------------
class ReconcileAction(Action):
    @Action.action
    def cb_action(self, uinfo, name, kp, input, output, trans):
        self.log.info('action name: ', name)
        self.log.info(f'kp:{kp}')
        with ncs.maapi.Maapi() as m:
            with ncs.maapi.Session(m,'admin', 'system'):
                with m.start_read_trans() as t_write:
                    root = ncs.maagic.get_root(t_write) # get maagic object
                    service = ncs.maagic.cd(root,kp)  # move to service
                    redeploy_inputs = service.re_deploy.get_input()
                    redeploy_inputs.reconcile.create() # manually set inputs
                    if input.dry_run:
                        redeploy_inputs.dry_run.create()

                        redeploy_inputs.dry_run.outformat="native"
                    if input.no_networking:
                        redeploy_inputs.no_networking.create()
                    redeploy_outputs = service.re_deploy(redeploy_inputs)
                    self.log.debug(f'output: {str(redeploy_outputs)}')
                    tag_output = redeploy_outputs._tagvalues()
                    self.log.debug(f'output: {str(tag_output)}')
                    output._from_tagvalues(tag_output)

class ReconcileFullAction(Action):
    @Action.action
    def cb_action(self, uinfo, name, kp, input, output, trans):
        self.log.info('action name: ', name)
        self.log.info(f'kp:{kp}')
        with ncs.maapi.Maapi() as m:
            with ncs.maapi.Session(m,'admin', 'system'):
                with m.start_read_trans() as t_write:
                    root = ncs.maagic.get_root(t_write)
                    service = ncs.maagic.cd(root,kp)
                    redeploy_outputs=service.re_deploy(input) # use same inputs as they have been sanitized in YANG file
                    self.log.info(f'output: {str(redeploy_outputs)}')
                    tag_output = redeploy_outputs._tagvalues()
                    self.log.debug(f'output: {str(tag_output)}')
                    output._from_tagvalues(tag_output)
# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class ServiceCallbacks(Service):

    # The create() callback is invoked inside NCS FASTMAP and
    # must always exist.
    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        self.log.info('Service create(service=', service._path, ')')


    # The pre_modification() and post_modification() callbacks are optional,
    # and are invoked outside FASTMAP. pre_modification() is invoked before
    # create, update, or delete of the service, as indicated by the enum
    # ncs_service_operation op parameter. Conversely
    # post_modification() is invoked after create, update, or delete
    # of the service. These functions can be useful e.g. for
    # allocations that should be stored and existing also when the
    # service instance is removed.

    # @Service.pre_lock_create
    # def cb_pre_lock_create(self, tctx, root, service, proplist):
    #     self.log.info('Service plcreate(service=', service._path, ')')

    # @Service.pre_modification
    # def cb_pre_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service premod(service=', kp, ')')

    # @Service.post_modification
    # def cb_post_modification(self, tctx, op, kp, root, proplist):
    #     self.log.info('Service postmod(service=', kp, ')')


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    def setup(self):
        # The application class sets up logging for us. It is accessible
        # through 'self.log' and is a ncs.log.Log instance.
        self.log.info('Main RUNNING')

        # Service callbacks require a registration for a 'service point',
        # as specified in the corresponding data model.
        #
        self.register_service('reconcile-keep-servicepoint', ServiceCallbacks)

        # When using actions, this is how we register them:
        #
        self.register_action('reconcile-keep-action', ReconcileAction)
        self.register_action('reconcile-keep-action-full', ReconcileFullAction)

        # If we registered any callback(s) above, the Application class
        # took care of creating a daemon (related to the service/action point).

        # When this setup method is finished, all registrations are
        # considered done and the application is 'started'.

    def teardown(self):
        # When the application is finished (which would happen if NCS went
        # down, packages were reloaded or some error occurred) this teardown
        # method will be called.

        self.log.info('Main FINISHED')
