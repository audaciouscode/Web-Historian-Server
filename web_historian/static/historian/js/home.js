//Load common code that includes config, then load the app logic for this page.
requirejs(['../../pdk/js/common'], function (common) {
    requirejs(["bootstrap", "bootstrap-typeahead", "bootstrap-table"], function (bootstrap, bs_typeahead, bs_table)
    {
		$('[data-toggle="tooltip"]').tooltip();
	}); 
});