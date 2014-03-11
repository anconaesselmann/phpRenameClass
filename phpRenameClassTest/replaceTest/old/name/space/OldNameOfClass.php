<?php
namespace old\name\space {
	class OldNameOfClass {
		public function test() {
			$instantiation = new OldNameOfClass();
			$static = OldNameOfClass::$test;
			$fullyNamespacedInstantiation = new \old\name\space\OldNameOfClass();
			$fullyNamespacedInstantiation = \old\name\space\OldNameOfClass::$test;
		}
	}
}