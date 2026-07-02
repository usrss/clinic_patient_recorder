from django.apps import AppConfig, apps
from django.db.models.signals import post_save, post_delete


class AuditLogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit_logs'
    verbose_name = 'Audit Logs'

    def ready(self):
        # Connect signal handlers to specific whitelisted models only
        # (instead of using catch-all @receiver decorators) to avoid
        # running audit logic on every single model save in the project.
        from .signals import audit_log_post_save, audit_log_post_delete, MODEL_MODULE_MAP

        for model_label in MODEL_MODULE_MAP:
            try:
                app_label, model_name = model_label.split('.')
                model = apps.get_model(app_label, model_name)
                if model is not None:
                    post_save.connect(audit_log_post_save, sender=model, weak=False)
                    post_delete.connect(audit_log_post_delete, sender=model, weak=False)
            except LookupError:
                # Model may not be available during initial migrations
                pass
