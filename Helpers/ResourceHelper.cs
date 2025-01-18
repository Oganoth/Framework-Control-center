using Avalonia;
using Avalonia.Media.Imaging;
using Avalonia.Platform;
using System;

namespace FrameworkControl.Helpers
{
    public static class ResourceHelper
    {
        public static Bitmap? LoadBitmapFromResource(string resourcePath)
        {
            try
            {
                var assets = AssetLoader.Open(new Uri($"avares://FrameworkControl/{resourcePath}"));
                return new Bitmap(assets);
            }
            catch (Exception)
            {
                return null;
            }
        }
    }
}
