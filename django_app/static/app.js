(function () {
    $(function () {
        $('.related-widget-wrapper select').addClass('form-control select2');
        $('.related-widget-wrapper select').select2({});
        $('.select2').select2({});

        $('.datepicker').datepicker({
            autoclose: true,
            format: 'dd/mm/yyyy'
        });

        $('.timepicker').timepicker({
            showInputs: false
        });

        $('.js-toggle-advance-search').on('click', function () {
            $(this).closest('.box').find('.advance-search-control-container').toggleClass('hide');
            $(this).find('i').toggleClass('fa-angle-double-down');
            $(this).find('i').toggleClass('fa-angle-double-right');
        });

        $(document).off('click').on('click', '.js-btn-util-delete', function () {
            let url = $(this).attr('data-url');
            $.confirm({
                title: 'Thông báo',
                animation: 'opacity',
                animationSpeed: 100,
                content: `<form method="post" action="` + url + `"><input type="hidden" name="csrfmiddlewaretoken" value="tVb0pm3nGnbtb87aOOzRz49A3hILlw5KW5KZhDHeui20Ex7EBu0GX6GW5GNHFo72">
                            <div>
                            <p>Bạn có chắc chắn muốn xóa bản ghi này?</p>
                            <input type="hidden" name="post" value="yes">
<!--                            <input type="submit" class="btn btn-primary" value="Xác nhận">-->
                            </div>
                           </form>`,
                buttons: {
                    formSubmit: {
                        text: 'Xác nhận',
                        btnClass: 'btn-primary',
                        action: function () {
                            let form = this.$content.find('form');
                            form.submit();
                        }
                    },
                    cancel: {
                        text: 'Hủy',
                        btnClass: 'btn-default',
                        action: function () {
                            return true;
                        }
                    },
                },
            })
        });

        $(document).on('change', '.js-change-page-size', function () {
            if ($('select[name=action]').length > 0) {
                $('select[name=action]').val('change_page_size');
            } else {
                // if there isn't action dropdown => create one
                $(this).closest('form#changelist-form').append(`<select name="action" class="hide">
                                                                    <option value="change_page_size" selected></option>
                                                                </select>`);
            }
            $(this).closest('form#changelist-form').submit();
        });

        $(document).on('submit', 'form.advance-search-form', function (e) {
            let formData = $(this).serializeArray();
            let formValueToSubmit = "";
            for (let i = 0; i < formData.length; i++) {
                formValueToSubmit += ",," + formData[i].name + "=" + formData[i].value
            }
            $(this).find('[name]').removeAttr('name');
            $(this).append('<input type="hidden" name="q" value="' + formValueToSubmit + '" />');
            return true;
        });
    });
})();