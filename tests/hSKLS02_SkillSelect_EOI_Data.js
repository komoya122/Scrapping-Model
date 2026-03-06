/*
 * Bootstrap-based responsive mashup
 * @owner Enter you name here (xxx)
 */
/*
 *    Fill in host and port for Qlik engine
 */
var prefix = window.location.pathname.substr( 0, window.location.pathname.toLowerCase().lastIndexOf( "/extensions" ) + 1 );

var config = {
	host: window.location.hostname,
	prefix: prefix,
	port: window.location.port,
	isSecure: window.location.protocol === "https:"
};

var app;
require.config( {
	baseUrl: (config.isSecure ? "https://" : "http://" ) + config.host + (config.port ? ":" + config.port : "" ) + config.prefix + "resources"
} );

require( ["js/qlik"], function ( qlik ) {

	var control = false;
	qlik.setOnError( function ( error ) {
		if(error.message == "Access denied"){
			window.location.href="AccessDenied.html";
		}else{
			$( '#popupText' ).append( error.message + "<br>" );
			if ( !control ) {
				control = true;
				$( '#popup' ).delay( 1000 ).fadeIn( 1000 ).delay( 11000 ).fadeOut( 1000 );
			}			
		}
	} );
	
	function AppUi ( app ) {
		var me = this;
		this.app = app;
		app.global.isPersonalMode( function ( reply ) {
			me.isPersonalMode = reply.qReturn;
		} );
		app.getAppLayout( function ( layout ) {
			$( "#title" ).attr( "title", "Last reload:" + layout.qLastReloadTime.replace( /T/, ' ' ).replace( /Z/, ' ' ) );
		} );
		$( "[data-qcmd]" ).on( 'click', function () {
			$('#page-container').removeClass('in');
			$('#page-loader').addClass('in');			
			var $element = $( this );
			var pageCurrent=0;
			var pageTotal=0;
			switch ( $element.data( 'qcmd' ) ) {
				case 'navBack':
				  	pageCurrent = parseInt($("#pagetitle")[0].dataset.current);
					if(pageCurrent>0){
						pageCurrent = pageCurrent-1;
					}else{
						pageCurrent = $('.navigate>li').children().length-1;
					}
					$('#f1').attr('src',$('.navigate>li').children()[pageCurrent].dataset.pagesource);	
					$( "#pagetitle" ).html($('.navigate>li').children()[pageCurrent].text);		
					FixSelected(pageCurrent);
					break;
				case 'navNext':
				  	pageCurrent = parseInt($("#pagetitle")[0].dataset.current);
					if(pageCurrent == $('.navigate>li').children().length-1){
						pageCurrent = 0;
					}else{
						pageCurrent = pageCurrent+1;
					}
					$('#f1').attr('src',$('.navigate>li').children()[pageCurrent].dataset.pagesource);	
					$( "#pagetitle" ).html($('.navigate>li').children()[pageCurrent].text);		
					FixSelected(pageCurrent);
					break;
			}
		});
		
		$('.navigate').on('click','li', function (e) {
			FixSelected($(this).index());    
			$('#f1').attr('src',$(this).children().data('pagesource'));	
			$("#pagetitle").html($(this).text());
			$("#pagetitle").attr('data-current',$(this).index());	
			$('#page-container').removeClass('in');
			$('#page-loader').addClass('in');				
		});
		
		$('.exportnavigate').on('click','li>a', function (e) {	
			var object = app.getObject($(this).attr('data-exportobj'));
			object.then(function(model) { 
				var table = new qlik.table(model); 
				table.exportData({download: false},function (link) {    
						var url = (config.isSecure ? "https://" : "http://") + config.host + (config.port ? ":" + config.port : "") + link    
						window.open(url, "_self");  
					});
				});			
		});		
		
		$('.exportnavigatesingle').on('click','a', function (e) {	
			var object = app.getObject($(this).attr('data-exportobj'));
			object.then(function(model) { 
				var table = new qlik.table(model); 
				table.exportData({download: false},function (link) {    
						var url = (config.isSecure ? "https://" : "http://") + config.host + (config.port ? ":" + config.port : "") + link    
						window.open(url, "_self");  
					});
				});			
		});			
	}
	
	/* TODO: Change the value inside qlik.openApp() to the App ID*/
	var app = qlik.openApp('aaac76b5-ad30-477e-9ca0-472f8ab57fc8', config);
	app.getObject('CurrentSelections','CurrentSelections');
	app.bookmark.apply('44604edb-b94c-414b-b978-30bb79019ffd');
	if ( app ) {
		new AppUi( app );
	}
	
	$(document).ready(function () {
		/* TODO: Change the Title */
		$(".appTitle").html("SkillSelect"); 
		
		var arraySheet = [
			/* TODO: Change the texts for sheetUrl and sheetText; add more {} blocks as required */
			{
				sheetUrl: "https://api.dynamic.reports.employment.gov.au/anonap/single/?appid=aaac76b5-ad30-477e-9ca0-472f8ab57fc8&sheet=ef6d431d-5689-4883-a3a8-860c7a258923",
				sheetText: "Dashboard Overview"
			},
			/* END TODO: Change the texts for sheetUrl and sheetText; add more {} blocks as required */
			
			{
				sheetUrl: "https://api.dynamic.reports.employment.gov.au/anonap/single/?appid=aaac76b5-ad30-477e-9ca0-472f8ab57fc8&sheet=799018bf-5805-4685-8f99-2af996e08197",
				sheetText: "EOI Parameters"
			},			
			{
				sheetUrl: "https://api.dynamic.reports.employment.gov.au/anonap/single/?appid=aaac76b5-ad30-477e-9ca0-472f8ab57fc8&sheet=1fbfd90f-e36c-44b9-a078-a7c78a46792c&opt=ctxmenu",
				sheetText: "Dashboard Results Table: EOI by Visa Type and Status"
			},		
			{
				sheetUrl: "https://api.dynamic.reports.employment.gov.au/anonap/single/?appid=aaac76b5-ad30-477e-9ca0-472f8ab57fc8&sheet=d8e3c4e6-6e84-42d2-bf62-82a2bab79d63",
				sheetText: "Help and How To's"
			},				
			
		];
		
		var sheetUrl = "";
		$.each(arraySheet, function(key, value) {
			//sheetUrl = value.sheetUrl + "&opt=ctxmenu";
			sheetUrl = value.sheetUrl;
			$('.navigate').append($("<li><a class='qcmd' data-qcmd='navClick' data-pagesource='"+sheetUrl+"'>"+value.sheetText+"</a></li>"));
		});		

		if(arraySheet.length == 1)
			$(".multi-sheets").css("display","none");

		$('#f1').attr('src',$('.navigate>li').children().first().attr('data-pagesource'));	
		$( "#pagetitle" ).html($('.navigate>li').children().first().text());		
		$('.navigate').children().first().addClass("menu-selected");        
		
		var arrayExport = [
			/* TODO: Change the texts for exportobj to ObjectId and exporttext to display name; add more {} blocks as required */
			//{
			//	exportobj: "30a43baa-7523-45bf-a3f8-4420f1e49852",
			//	exporttext: "Export Data"
			//},
			/* END TODO: Change the texts for exportobj to ObjectId and exporttext to display name; add more {} blocks as required */		
			
		];
		if(arrayExport.length==0){
			$(".exportlink").css("display","none");
		}else if(arrayExport.length==1){
			$(".exportlink").css("display","none");
			$.each(arrayExport, function(key, value) {
				$('.exportnavigatesingle').append($("<a data-exportObj='"+value.exportobj+"'>"+value.exporttext+"</a>"));
			});			
		}else{
			$(".exportnavigatesingle").css("display","none");
			$.each(arrayExport, function(key, value) {
				$('.exportnavigate').append($("<li><a data-exportObj='"+value.exportobj+"'>"+value.exporttext+"</a></li>"));
			});	
		}	
			
	});
	
	$('#f1').on( 'load', function() {
		$('#page-container').addClass('in');
		$('#page-loader').removeClass('in');		
		$("#f1").contents().find("head").append($("<style type='text/css'>    div.single-object #content{padding-top:10px;}  </style>"))
	} );	

	function FixSelected(i){
		$('.navigate>li').each(function(index) {
			if(index == i)
			{
				$(this).addClass("menu-selected"); 
				$("#pagetitle").attr('data-current',index);
			}
			else
			{
				$(this).removeClass("menu-selected");   
			}
		});	
	}	

} );

