# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Order'
        db.create_table('cart_order', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('hash', self.gf('django.db.models.fields.CharField')(unique=True, max_length=16)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(default='', max_length=75, blank=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(default='', max_length=20, blank=True)),
            ('street_address', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('suburb', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('post_code', self.gf('django.db.models.fields.CharField')(default='', max_length=20, blank=True)),
            ('country', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='pending', max_length=20)),
            ('payment_successful', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('notification_sent', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('acknowledgement_sent', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('payment_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('completion_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('session_id', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('shipping_cost', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=10, decimal_places=2)),
        ))
        db.send_create_signal('cart', ['Order'])

        # Adding model 'OrderLine'
        db.create_table('cart_orderline', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cart.Order'])),
            ('product_content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('product_object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('quantity', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2)),
            ('options', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal('cart', ['OrderLine'])

        # Adding model 'PaymentAttempt'
        db.create_table('cart_paymentattempt', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cart.Order'])),
            ('hash', self.gf('django.db.models.fields.CharField')(unique=True, max_length=16)),
            ('result', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('user_message', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('transaction_ref', self.gf('django.db.models.fields.CharField')(default='', max_length=32, blank=True)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(default=0, max_digits=10, decimal_places=2)),
            ('success', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('cart', ['PaymentAttempt'])


    def backwards(self, orm):
        # Deleting model 'Order'
        db.delete_table('cart_order')

        # Deleting model 'OrderLine'
        db.delete_table('cart_orderline')

        # Deleting model 'PaymentAttempt'
        db.delete_table('cart_paymentattempt')


    models = {
        'cart.order': {
            'Meta': {'ordering': "('-creation_date',)", 'object_name': 'Order'},
            'acknowledgement_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'city': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'completion_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'default': "''", 'max_length': '75', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'notification_sent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'payment_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'payment_successful': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'phone': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'post_code': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '20', 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'shipping_cost': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '2'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '20'}),
            'street_address': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'suburb': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'})
        },
        'cart.orderline': {
            'Meta': {'object_name': 'OrderLine'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'options': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cart.Order']"}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'product_content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'product_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'cart.paymentattempt': {
            'Meta': {'ordering': "('-creation_date',)", 'object_name': 'PaymentAttempt'},
            'amount': ('django.db.models.fields.DecimalField', [], {'default': '0', 'max_digits': '10', 'decimal_places': '2'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cart.Order']"}),
            'result': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'success': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'transaction_ref': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '32', 'blank': 'True'}),
            'user_message': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['cart']