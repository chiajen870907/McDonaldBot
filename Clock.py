from apscheduler.schedulers.blocking import BlockingScheduler
from app import McDonald_AutoLottery_Coupon
from app import McDonald_AutoLottery_Sticker

sched = BlockingScheduler()
@sched.scheduled_job('cron', hour=0, minute=5)
def scheduled_job():
    McDonald_AutoLottery_Coupon()
    McDonald_AutoLottery_Sticker()


sched.start()




