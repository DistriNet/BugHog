package {
	import flash.display.Sprite;
	import flash.events.Event;
	import flash.external.ExternalInterface;
	import flash.net.URLLoader;
	import flash.net.URLRequest;
	public class tester extends Sprite
	{
		public var loader:URLLoader=new URLLoader();;
		public function tester()
		{
			var request:URLRequest = new URLRequest("https://adition.com/");
			ExternalInterface.call("alert");
			this.loader.load(request);
		}
	}
}