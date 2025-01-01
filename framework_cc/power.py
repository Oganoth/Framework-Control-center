from typing import List
import asyncio
import subprocess
import logging

logger = logging.getLogger(__name__)

class Power:
    async def _run_ryzenadj(self, args: List[str]) -> bool:
        """Run RyzenADJ with the specified arguments."""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = await asyncio.create_subprocess_exec(
                str(self.ryzenadj_path),
                *args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info("RyzenAdj configured successfully")
                return True
            else:
                logger.error(f"RyzenAdj failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error running RyzenAdj: {e}")
            return False 