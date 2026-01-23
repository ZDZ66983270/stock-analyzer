@app.post("/api/force-refresh")
async def force_refresh(background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    强制刷新所有自选股数据
    - 开市期间：获取最新分钟数据
    - 闭市后：获取最新日线数据
    """
    from market_status import is_market_open
    from data_fetcher import DataFetcher
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 获取所有自选股
    watchlist = list(session.exec(select(Watchlist)).all())
    
    if not watchlist:
        return {
            "status": "success",
            "message": "自选列表为空",
            "refreshed": 0
        }
    
    # 后台任务：刷新所有股票
    def refresh_all_stocks():
        fetcher = DataFetcher()
        success_count = 0
        failed_count = 0
        
        for item in watchlist:
            try:
                market_open = is_market_open(item.market)
                
                if market_open:
                    # 开市：获取分钟数据
                    logger.info(f"[强制刷新] {item.symbol} ({item.market}) - 开市中，获取分钟数据")
                    result = fetcher.fetch_latest_data(
                        item.symbol,
                        item.market,
                        force_refresh=True,
                        save_db=True
                    )
                else:
                    # 闭市：获取日线数据
                    logger.info(f"[强制刷新] {item.symbol} ({item.market}) - 已闭市，获取日线数据")
                    result = fetcher.fetch_latest_data(
                        item.symbol,
                        item.market,
                        force_refresh=True,
                        save_db=True
                    )
                
                if result:
                    success_count += 1
                    logger.info(f"✅ [强制刷新] {item.symbol} 成功")
                else:
                    failed_count += 1
                    logger.warning(f"⚠️ [强制刷新] {item.symbol} 失败")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ [强制刷新] {item.symbol} 异常: {e}")
        
        logger.info(
            f"[强制刷新] 完成 - 成功: {success_count}, 失败: {failed_count}, "
            f"总计: {len(watchlist)}"
        )
    
    # 添加后台任务
    background_tasks.add_task(refresh_all_stocks)
    
    return {
        "status": "success",
        "message": f"已触发强制刷新，正在后台处理{len(watchlist)}只股票",
        "total": len(watchlist)
    }
