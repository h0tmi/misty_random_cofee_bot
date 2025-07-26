# Shared objects for the bot application

# Global scheduler instance
_global_scheduler = None


def set_scheduler(scheduler):
    """Set the global scheduler instance"""
    global _global_scheduler
    _global_scheduler = scheduler


def get_scheduler():
    """Get the global scheduler instance"""
    return _global_scheduler